"""create campaigns and calls tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-28

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Phone Numbers
    op.create_table(
        "phone_numbers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("e164", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("trunk_id", sa.String(length=255), nullable=False),
        sa.Column("attestation", sa.String(length=10), nullable=True),
        sa.Column("cnam_status", sa.String(length=20), nullable=True),
        sa.Column("daily_cap", sa.Integer(), server_default="100", nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_phone_numbers_e164"), "phone_numbers", ["e164"], unique=False)
    op.create_index(op.f("ix_phone_numbers_tenant_id"), "phone_numbers", ["tenant_id"], unique=False)

    # Campaigns
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("script_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("number_pool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voice_config", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("calling_window", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("retry_policy", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_campaigns_tenant_id"), "campaigns", ["tenant_id"], unique=False)

    # Script Versions
    op.create_table(
        "script_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("allowed_topics", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("tools", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_versions_tenant_id"), "script_versions", ["tenant_id"], unique=False)

    # Campaign Contacts
    op.create_table(
        "campaign_contacts",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(length=20), server_default="queued", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_outcome", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
        ),
        sa.ForeignKeyConstraint(
            ["contact_id"],
            ["contacts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("campaign_id", "contact_id"),
    )
    op.create_index(op.f("ix_campaign_contacts_tenant_id"), "campaign_contacts", ["tenant_id"], unique=False)

    # Calls
    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("number_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_s", sa.Integer(), nullable=True),
        sa.Column("recording_uri", sa.String(length=1024), nullable=True),
        sa.Column("transcript_uri", sa.String(length=1024), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("extracted", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("rule_decision", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("cost_inr", sa.Numeric(precision=12, scale=4), server_default="0.0000", nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calls_tenant_id"), "calls", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_calls_campaign_id"), "calls", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_calls_contact_id"), "calls", ["contact_id"], unique=False)

    # Call Events
    op.create_table(
        "call_events",
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(
            ["call_id"],
            ["calls.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("call_id", "ts", "type"),
    )
    op.create_index(op.f("ix_call_events_tenant_id"), "call_events", ["tenant_id"], unique=False)

    # RLS Policies
    op.execute("ALTER TABLE phone_numbers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE phone_numbers FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON phone_numbers USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE campaigns FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON campaigns USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE script_versions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE script_versions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON script_versions USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE campaign_contacts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE campaign_contacts FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON campaign_contacts USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE calls ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE calls FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON calls USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE call_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE call_events FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON call_events USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )


def downgrade() -> None:
    op.drop_table("call_events")
    op.drop_table("calls")
    op.drop_table("campaign_contacts")
    op.drop_table("script_versions")
    op.drop_table("campaigns")
    op.drop_table("phone_numbers")
