"""Conversation and call domain models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin

if TYPE_CHECKING:
    from datetime import datetime


class Call(Base, TenantMixin):
    """A phone call."""

    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    number_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    direction: Mapped[str] = mapped_column(sa.String(10), nullable=False)  # inbound, outbound
    mode: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    outcome: Mapped[str | None] = mapped_column(sa.String(50))

    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
    answered_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    duration_s: Mapped[int | None] = mapped_column(sa.Integer)

    recording_uri: Mapped[str | None] = mapped_column(sa.String(1024))
    transcript_uri: Mapped[str | None] = mapped_column(sa.String(1024))

    summary: Mapped[str | None] = mapped_column(sa.Text)
    extracted: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    rule_decision: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    cost_inr: Mapped[float] = mapped_column(sa.Numeric(12, 4), server_default="0.0000", nullable=False)


class CallEvent(Base, TenantMixin):
    """An event during a call."""

    __tablename__ = "call_events"
    __table_args__ = (sa.PrimaryKeyConstraint("call_id", "ts", "type"),)

    call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("calls.id"), nullable=False)
    ts: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)
    type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
