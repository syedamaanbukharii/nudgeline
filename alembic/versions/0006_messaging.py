"""create messaging tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-28

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Sequences
    op.create_table(
        "sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("stop_rules", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sequences_tenant_id"), "sequences", ["tenant_id"], unique=False)

    # Sequence Enrollments
    op.create_table(
        "sequence_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rep_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("current_step", sa.Integer(), server_default="0", nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["contact_id"],
            ["contacts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rep_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sequence_id"],
            ["sequences.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sequence_enrollments_tenant_id"), "sequence_enrollments", ["tenant_id"], unique=False)

    # Email Messages
    op.create_table(
        "email_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rep_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["contact_id"],
            ["contacts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["sequence_enrollments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rep_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_messages_tenant_id"), "email_messages", ["tenant_id"], unique=False)

    # RLS Policies
    op.execute("ALTER TABLE sequences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sequences FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON sequences USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE sequence_enrollments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sequence_enrollments FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON sequence_enrollments USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE email_messages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_messages FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON email_messages USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )


def downgrade() -> None:
    op.drop_table("email_messages")
    op.drop_table("sequence_enrollments")
    op.drop_table("sequences")
