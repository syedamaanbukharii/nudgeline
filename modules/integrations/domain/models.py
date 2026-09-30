"""Integration domain models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin

if TYPE_CHECKING:
    from datetime import datetime


class Integration(Base, TenantMixin):
    """A configured integration for a tenant (e.g. HubSpot, GoHighLevel)."""

    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="active", nullable=False)

    # Encrypted credentials (OAuth tokens, API keys)
    credentials_enc: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)

    config: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.func.now(), nullable=False
    )


class WebhookSubscription(Base, TenantMixin):
    """Inbound webhook configurations."""

    __tablename__ = "webhook_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    events: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)

    # The secret used to verify incoming webhook signatures
    secret_enc: Mapped[bytes | None] = mapped_column(sa.LargeBinary)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
