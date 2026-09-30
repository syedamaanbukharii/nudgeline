"""create contacts and compliance tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-28

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Companies
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_tenant_id"), "companies", ["tenant_id"], unique=False)

    # Contacts
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("phone_enc", sa.LargeBinary(), nullable=True),
        sa.Column("phone_hash", sa.LargeBinary(), nullable=True),
        sa.Column("email_enc", sa.LargeBinary(), nullable=True),
        sa.Column("email_hash", sa.LargeBinary(), nullable=True),
        sa.Column("timezone", sa.String(length=50), server_default="UTC", nullable=False),
        sa.Column("country", sa.String(length=2), server_default="US", nullable=False),
        sa.Column("line_type", sa.String(length=20), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("attrs", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contacts_tenant_id"), "contacts", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_contacts_phone_hash"), "contacts", ["phone_hash"], unique=False)
    op.create_index(op.f("ix_contacts_email_hash"), "contacts", ["email_hash"], unique=False)

    # Consents
    op.create_table(
        "consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("consent_type", sa.String(length=50), nullable=False),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("evidence_uri", sa.String(length=1024), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["contact_id"],
            ["contacts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_consents_tenant_id"), "consents", ["tenant_id"], unique=False)

    # DNC Entries
    op.create_table(
        "dnc_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("phone_hash", sa.LargeBinary(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dnc_entries_phone_hash"), "dnc_entries", ["phone_hash"], unique=False)
    op.create_index(op.f("ix_dnc_entries_tenant_id"), "dnc_entries", ["tenant_id"], unique=False)

    # External Refs
    op.create_table(
        "external_refs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "provider", "entity_type", "external_id", name="uq_external_refs"),
    )
    op.create_index(op.f("ix_external_refs_tenant_id"), "external_refs", ["tenant_id"], unique=False)

    # Rule Packs
    op.create_table(
        "rule_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jurisdiction", "version", name="uq_rule_packs_jurisdiction_version"),
    )

    # RLS Policies
    op.execute("ALTER TABLE companies ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE companies FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON companies USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE contacts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE contacts FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON contacts USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE consents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE consents FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON consents USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )

    op.execute("ALTER TABLE dnc_entries ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dnc_entries FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON dnc_entries USING (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )

    op.execute("ALTER TABLE external_refs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE external_refs FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_policy ON external_refs USING (tenant_id = current_setting('app.tenant_id')::uuid)"
    )


def downgrade() -> None:
    op.drop_table("rule_packs")
    op.drop_table("external_refs")
    op.drop_table("dnc_entries")
    op.drop_table("consents")
    op.drop_table("contacts")
    op.drop_table("companies")
