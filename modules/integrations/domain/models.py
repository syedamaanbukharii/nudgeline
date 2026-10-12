"""Per-tenant connections to stores, WhatsApp and telephony."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin, TimestampMixin

PROVIDERS = ("shopify", "webhook", "whatsapp", "telephony")


class Integration(Base, TimestampMixin, TenantMixin):
    """Secrets are encrypted with the tenant's data key; `config` holds only non-secret values."""

    __tablename__ = "integrations"
    __table_args__ = (sa.UniqueConstraint("tenant_id", "provider", name="uq_integrations_tenant_provider"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="active", nullable=False)
    public_token: Mapped[str] = mapped_column(sa.String(64), unique=True, nullable=False)
    credentials_enc: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    last_event_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(sa.Text)
