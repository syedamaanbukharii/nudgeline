"""create teams table and add team_id to users

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-28

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Teams
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("target_calls", sa.Integer(), server_default="100", nullable=False),
        sa.Column("target_meetings", sa.Integer(), server_default="5", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_teams_tenant_id"), "teams", ["tenant_id"], unique=False)

    # Add team_id to users
    op.add_column("users", sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_users_team_id", "users", "teams", ["team_id"], ["id"])

    # RLS for Teams
    op.execute("ALTER TABLE teams ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE teams FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON teams USING (tenant_id = current_setting('app.tenant_id')::uuid)")


def downgrade() -> None:
    op.drop_constraint("fk_users_team_id", "users", type_="foreignkey")
    op.drop_column("users", "team_id")
    op.drop_table("teams")
