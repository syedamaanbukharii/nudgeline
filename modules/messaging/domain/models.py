"""Messaging domain models for emails and sequences."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin

if TYPE_CHECKING:
    from datetime import datetime


class Sequence(Base, TenantMixin):
    """An automated follow-up sequence."""

    __tablename__ = "sequences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    steps: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="[]", nullable=False)
    stop_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


class SequenceEnrollment(Base, TenantMixin):
    """A contact's enrollment in a sequence."""

    __tablename__ = "sequence_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("sequences.id"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=False)
    rep_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False)

    state: Mapped[str] = mapped_column(sa.String(20), server_default="active", nullable=False)
    current_step: Mapped[int] = mapped_column(sa.Integer, server_default="0", nullable=False)

    enrolled_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


class EmailMessage(Base, TenantMixin):
    """An email draft or sent message."""

    __tablename__ = "email_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=False)
    rep_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False)
    enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("sequence_enrollments.id")
    )

    status: Mapped[str] = mapped_column(sa.String(20), server_default="draft", nullable=False)
    subject: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)

    provider_message_id: Mapped[str | None] = mapped_column(sa.String(255))
    thread_id: Mapped[str | None] = mapped_column(sa.String(255))

    sent_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    replied_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )
