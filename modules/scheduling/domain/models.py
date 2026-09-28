"""Scheduling domain models."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin


class Meeting(Base, TenantMixin):
    """A booked meeting."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("calls.id")
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=False
    )
    rep_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
    )
    
    provider: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    external_event_id: Mapped[str | None] = mapped_column(sa.String(255))
    
    starts_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    join_url: Mapped[str | None] = mapped_column(sa.String(1024))
    
    status: Mapped[str] = mapped_column(sa.String(20), server_default="scheduled", nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(sa.String(128), unique=True)


class Reminder(Base, TenantMixin):
    """A callback or follow-up reminder."""

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=False
    )
    call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("calls.id")
    )
    rep_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
    )
    
    due_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="pending", nullable=False)
    note: Mapped[str | None] = mapped_column(sa.Text)
