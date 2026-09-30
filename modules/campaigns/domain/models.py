"""Campaign domain models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from datetime import datetime


class PhoneNumber(Base, TenantMixin):
    """A phone number registered to a tenant."""

    __tablename__ = "phone_numbers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    e164: Mapped[str] = mapped_column(sa.String(20), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    trunk_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    attestation: Mapped[str | None] = mapped_column(sa.String(10))
    cnam_status: Mapped[str | None] = mapped_column(sa.String(20))
    daily_cap: Mapped[int] = mapped_column(sa.Integer, server_default="100", nullable=False)


class Campaign(Base, TimestampMixin, TenantMixin):
    """An outbound calling campaign."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    mode: Mapped[str] = mapped_column(sa.String(10), nullable=False)  # A, B, or C
    status: Mapped[str] = mapped_column(sa.String(20), server_default="draft", nullable=False)

    script_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    number_pool_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    voice_config: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    calling_window: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    retry_policy: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)


class ScriptVersion(Base, TimestampMixin, TenantMixin):
    """A versioned script for a campaign."""

    __tablename__ = "script_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("campaigns.id"), nullable=False)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(sa.Text, nullable=False)
    allowed_topics: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)
    tools: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)

    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class CampaignContact(Base, TenantMixin):
    """A contact's enrollment in a campaign."""

    __tablename__ = "campaign_contacts"

    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("campaigns.id"), primary_key=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("contacts.id"), primary_key=True)
    state: Mapped[str] = mapped_column(sa.String(20), server_default="queued", nullable=False)
    attempts: Mapped[int] = mapped_column(sa.Integer, server_default="0", nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    last_outcome: Mapped[str | None] = mapped_column(sa.String(50))
