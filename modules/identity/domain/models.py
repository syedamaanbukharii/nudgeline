"""Users and tenant-defined roles."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin, TimestampMixin


class Role(Base, TimestampMixin, TenantMixin):
    """A named set of permissions, defined by each tenant."""

    __tablename__ = "roles"
    __table_args__ = (sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(60), nullable=False)
    description: Mapped[str] = mapped_column(sa.String(255), server_default="", nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSONB, server_default="[]", nullable=False)
    is_system: Mapped[bool] = mapped_column(sa.Boolean, server_default="false", nullable=False)


class User(Base, TimestampMixin, TenantMixin):
    """A person who signs in to a tenant. Email is unique across the platform."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(sa.String(320), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, server_default="true", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
