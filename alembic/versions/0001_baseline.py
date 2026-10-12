"""baseline: tenants, identity, workflows, integrations, compliance

Revision ID: 0001
Revises:
Create Date: 2026-10-12

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "nudgeline_app"
# Fail closed: with no tenant set, the comparison is NULL and no rows match.
TENANT_EXPR = "NULLIF(current_setting('app.tenant_id', true), '')::uuid"
TENANT_TABLES = (
    "roles",
    "users",
    "audit_log",
    "jobs",
    "integrations",
    "workflows",
    "workflow_runs",
    "run_attempts",
    "dnc_entries",
)


def _id() -> sa.Column:
    return sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def _tenant() -> sa.Column:
    return sa.Column(
        "tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )


def _ts(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "tenants",
        _id(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False, unique=True),
        sa.Column("country", sa.String(2), server_default="AE", nullable=False),
        sa.Column("timezone", sa.String(64), server_default="Asia/Dubai", nullable=False),
        sa.Column("currency", sa.String(3), server_default="AED", nullable=False),
        sa.Column("locale", sa.String(8), server_default="en", nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("settings", JSONB, server_default="{}", nullable=False),
        sa.Column("data_key_enc", sa.LargeBinary, nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_table(
        "roles",
        _id(),
        _tenant(),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("description", sa.String(255), server_default="", nullable=False),
        sa.Column("permissions", JSONB, server_default="[]", nullable=False),
        sa.Column("is_system", sa.Boolean, server_default="false", nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )
    op.create_table(
        "users",
        _id(),
        _tenant(),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_table(
        "audit_log",
        _id(),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("changes", JSONB),
        _ts("created_at"),
    )
    op.create_index("ix_audit_log_tenant_created", "audit_log", ["tenant_id", "created_at"])
    op.create_table(
        "jobs",
        _id(),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("payload", JSONB, server_default="{}", nullable=False),
        _ts("due_at"),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer, server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer, server_default="5", nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", sa.String(100)),
        sa.Column("last_error", sa.Text),
        _ts("created_at"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_jobs_due", "jobs", ["status", "due_at"])
    op.create_table(
        "integrations",
        _id(),
        _tenant(),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("public_token", sa.String(64), nullable=False, unique=True),
        sa.Column("credentials_enc", sa.LargeBinary, nullable=False),
        sa.Column("config", JSONB, server_default="{}", nullable=False),
        sa.Column("last_event_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("tenant_id", "provider", name="uq_integrations_tenant_provider"),
    )
    op.create_table(
        "workflows",
        _id(),
        _tenant(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("template_key", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("default_language", sa.String(4), server_default="auto", nullable=False),
        sa.Column("script", JSONB, nullable=False),
        sa.Column("settings", JSONB, nullable=False),
        sa.Column("created_by", UUID(as_uuid=True)),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_table(
        "workflow_runs",
        _id(),
        _tenant(),
        sa.Column("workflow_id", UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("external_ref", sa.String(120), nullable=False),
        sa.Column("order_number", sa.String(60), server_default="", nullable=False),
        sa.Column("contact_enc", sa.LargeBinary, nullable=False),
        sa.Column("phone_hash", sa.LargeBinary, nullable=False),
        sa.Column("phone_last4", sa.String(4), nullable=False),
        sa.Column("phone_country", sa.String(2)),
        sa.Column("contact_timezone", sa.String(64), nullable=False),
        sa.Column("language", sa.String(4), nullable=False),
        sa.Column("payload", JSONB, server_default="{}", nullable=False),
        sa.Column("status", sa.String(20), server_default="queued", nullable=False),
        sa.Column("status_reason", sa.String(60)),
        sa.Column("outcome_channel", sa.String(20)),
        sa.Column("outcome_at", sa.DateTime(timezone=True)),
        sa.Column("call_attempts", sa.Integer, server_default="0", nullable=False),
        sa.Column("whatsapp_sent_at", sa.DateTime(timezone=True)),
        sa.Column("next_action_at", sa.DateTime(timezone=True)),
        sa.Column("compliance_log", JSONB, server_default="[]", nullable=False),
        sa.Column("actions_status", sa.String(20)),
        sa.Column("actions_error", sa.Text),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("tenant_id", "workflow_id", "external_ref", name="uq_runs_workflow_ref"),
    )
    op.create_index("ix_runs_tenant_created", "workflow_runs", ["tenant_id", "created_at"])
    op.create_index("ix_runs_tenant_status", "workflow_runs", ["tenant_id", "status"])
    op.create_table(
        "run_attempts",
        _id(),
        _tenant(),
        sa.Column(
            "run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("attempt_no", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("digit", sa.String(4)),
        sa.Column("provider_ref", sa.String(120)),
        sa.Column("duration_seconds", sa.Integer),
        sa.Column("cost", sa.Numeric(12, 4)),
        sa.Column("currency", sa.String(3)),
        sa.Column("error", sa.Text),
        _ts("started_at"),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "dnc_entries",
        _id(),
        _tenant(),
        sa.Column("phone_hash", sa.LargeBinary, nullable=False),
        sa.Column("phone_last4", sa.String(4), nullable=False),
        sa.Column("reason", sa.String(40), server_default="manual", nullable=False),
        sa.Column("created_by", UUID(as_uuid=True)),
        _ts("created_at"),
        sa.UniqueConstraint("tenant_id", "phone_hash", name="uq_dnc_tenant_phone"),
    )

    # Row-level security
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY tenant_isolation ON tenants USING (id = {TENANT_EXPR})")
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation ON {table} USING (tenant_id = {TENANT_EXPR})")

    # The app role (created by infra/postgres init) gets data access only; RLS applies to it.
    op.execute(
        f"""
        DO $$
        BEGIN
          IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            GRANT USAGE ON SCHEMA public TO {APP_ROLE};
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE};
            REVOKE ALL ON alembic_version FROM {APP_ROLE};
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    for table in (
        "dnc_entries",
        "run_attempts",
        "workflow_runs",
        "workflows",
        "integrations",
        "jobs",
        "audit_log",
        "users",
        "roles",
        "tenants",
    ):
        op.drop_table(table)
