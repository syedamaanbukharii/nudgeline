"""create integrations tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-28

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Integrations
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("credentials_enc", sa.LargeBinary(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "provider", name="uq_integrations_tenant_provider")
    )
    op.create_index(op.f("ix_integrations_tenant_id"), "integrations", ["tenant_id"], unique=False)

    # Webhook Subscriptions
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("events", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("secret_enc", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_webhook_subscriptions_tenant_id"), "webhook_subscriptions", ["tenant_id"], unique=False)

    # RLS Policies
    op.execute("ALTER TABLE integrations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE integrations FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON integrations USING (tenant_id = current_setting('app.tenant_id')::uuid)")

    op.execute("ALTER TABLE webhook_subscriptions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE webhook_subscriptions FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON webhook_subscriptions USING (tenant_id = current_setting('app.tenant_id')::uuid)")


def downgrade() -> None:
    op.drop_table("webhook_subscriptions")
    op.drop_table("integrations")
