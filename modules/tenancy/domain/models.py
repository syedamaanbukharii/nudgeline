"""Core domain models and SQLAlchemy base."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
        uuid.UUID: UUID(as_uuid=True),
    }


class TimestampMixin:
    """Adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=text("now()"),
        nullable=False,
    )


class TenantMixin:
    """Adds tenant_id for RLS-protected tables."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )


class Tenant(Base, TimestampMixin):
    """Multi-tenant organization."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(63), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(sa.String(50), server_default="free", nullable=False)
    region: Mapped[str] = mapped_column(sa.String(10), server_default="in", nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="active", nullable=False)
    kyc_status: Mapped[str] = mapped_column(sa.String(20), server_default="pending", nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    data_key_enc: Mapped[bytes | None] = mapped_column(sa.LargeBinary)

    users: Mapped[list[User]] = relationship(back_populates="tenant")


class User(Base, TimestampMixin, TenantMixin):
    """User within a tenant."""

    __tablename__ = "users"
    __table_args__ = (sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(320), nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="rep"
    )  # owner, admin, manager, rep, viewer
    timezone: Mapped[str] = mapped_column(sa.String(50), server_default="Asia/Kolkata", nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, server_default="true", nullable=False)
    external_id: Mapped[str | None] = mapped_column(sa.String(255))  # Keycloak sub

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class APIKey(Base, TimestampMixin, TenantMixin):
    """Scoped API key for programmatic access."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash: Mapped[str] = mapped_column(sa.String(128), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(sa.String(12), nullable=False)  # nl_live_xxxx
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(sa.Boolean, server_default="true", nullable=False)


class OutboxEvent(Base):
    """Transactional outbox for reliable event publishing."""

    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    topic: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class ScheduledAction(Base):
    """Durable scheduled actions with SKIP LOCKED polling."""

    __tablename__ = "scheduled_actions"
    __table_args__ = (sa.Index("ix_scheduled_actions_due", "status", "due_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kind: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    due_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(20), server_default="pending", nullable=False
    )  # pending, locked, done, failed
    attempts: Mapped[int] = mapped_column(sa.Integer, server_default="0", nullable=False)
    locked_by: Mapped[str | None] = mapped_column(sa.String(100))
    locked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(sa.Text)


class IdempotencyRecord(Base):
    """Idempotency key store for POST deduplication."""

    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(sa.String(255), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_code: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)


class AuditLogEntry(Base):
    """Immutable audit trail."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(sa.String(45))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
