"""Contacts and compliance domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modules.tenancy.domain.models import Base, TimestampMixin, TenantMixin


class Company(Base, TimestampMixin, TenantMixin):
    """A company that a contact belongs to."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(sa.String(255))
    attrs: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    
    contacts: Mapped[list[Contact]] = relationship(back_populates="company")


class Contact(Base, TimestampMixin, TenantMixin):
    """A person to be contacted."""

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("companies.id")
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )
    
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(sa.String(255))
    
    phone_enc: Mapped[bytes | None] = mapped_column(sa.LargeBinary)
    phone_hash: Mapped[bytes | None] = mapped_column(sa.LargeBinary, index=True)
    email_enc: Mapped[bytes | None] = mapped_column(sa.LargeBinary)
    email_hash: Mapped[bytes | None] = mapped_column(sa.LargeBinary, index=True)
    
    timezone: Mapped[str] = mapped_column(sa.String(50), server_default="UTC", nullable=False)
    country: Mapped[str] = mapped_column(sa.String(2), server_default="US", nullable=False)
    line_type: Mapped[str | None] = mapped_column(sa.String(20))
    source: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    attrs: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    
    company: Mapped[Company | None] = relationship(back_populates="contacts")
    consents: Mapped[list[Consent]] = relationship(back_populates="contact")


class Consent(Base, TenantMixin):
    """Consent record for a contact."""

    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # voice, sms, email
    consent_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    
    evidence_uri: Mapped[str | None] = mapped_column(sa.String(1024))
    captured_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    
    contact: Mapped[Contact] = relationship(back_populates="consents")


class DNCEntry(Base):
    """Do Not Call list entries. tenant_id is nullable for global lists."""

    __tablename__ = "dnc_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("tenants.id"), index=True
    )
    phone_hash: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False, index=True)
    source: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


class ExternalRef(Base, TenantMixin):
    """Mapping to external systems (CRM, ATS, etc)."""

    __tablename__ = "external_refs"
    __table_args__ = (
        sa.UniqueConstraint("tenant_id", "provider", "entity_type", "external_id", name="uq_external_refs"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
