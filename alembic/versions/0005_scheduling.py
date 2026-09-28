"""create scheduling tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-28

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Meetings
    op.create_table(
        "meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rep_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_event_id", sa.String(length=255), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("join_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="scheduled", nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ),
        sa.ForeignKeyConstraint(["rep_user_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key")
    )
    op.create_index(op.f("ix_meetings_tenant_id"), "meetings", ["tenant_id"], unique=False)

    # Reminders
    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rep_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ),
        sa.ForeignKeyConstraint(["rep_user_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_reminders_tenant_id"), "reminders", ["tenant_id"], unique=False)

    # RLS Policies
    op.execute("ALTER TABLE meetings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE meetings FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON meetings USING (tenant_id = current_setting('app.tenant_id')::uuid)")

    op.execute("ALTER TABLE reminders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reminders FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON reminders USING (tenant_id = current_setting('app.tenant_id')::uuid)")


def downgrade() -> None:
    op.drop_table("reminders")
    op.drop_table("meetings")
