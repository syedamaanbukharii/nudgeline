"""Do-not-call list."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin


class DncEntry(Base, TenantMixin):
    """A phone number this tenant must never call. Stored only as a keyed hash."""

    __tablename__ = "dnc_entries"
    __table_args__ = (sa.UniqueConstraint("tenant_id", "phone_hash", name="uq_dnc_tenant_phone"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_hash: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    phone_last4: Mapped[str] = mapped_column(sa.String(4), nullable=False)
    reason: Mapped[str] = mapped_column(sa.String(40), server_default="manual", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
