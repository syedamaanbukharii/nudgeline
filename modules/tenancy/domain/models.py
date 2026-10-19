"""SQLAlchemy base, shared mixins, and platform tables (tenants, jobs, audit log)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), onupdate=sa.func.now(), nullable=False
    )


class TenantMixin:
    """Adds tenant_id for RLS-protected tables."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )


class Tenant(Base, TimestampMixin):
    """A customer organization."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(63), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(sa.String(2), server_default="AE", nullable=False)
    timezone: Mapped[str] = mapped_column(sa.String(64), server_default="Asia/Dubai", nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), server_default="AED", nullable=False)
    locale: Mapped[str] = mapped_column(sa.String(8), server_default="en", nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="active", nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    data_key_enc: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)


class Job(Base):
    """Durable background job, claimed by the worker with FOR UPDATE SKIP LOCKED."""

    __tablename__ = "jobs"
    __table_args__ = (sa.Index("ix_jobs_due", "status", "due_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    due_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=text("now()"), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(sa.Integer, server_default="0", nullable=False)
    max_attempts: Mapped[int] = mapped_column(sa.Integer, server_default="5", nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    locked_by: Mapped[str | None] = mapped_column(sa.String(100))
    last_error: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class AuditLogEntry(Base):
    """Append-only record of who changed what."""

    __tablename__ = "audit_log"
    __table_args__ = (sa.Index("ix_audit_log_tenant_created", "tenant_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
