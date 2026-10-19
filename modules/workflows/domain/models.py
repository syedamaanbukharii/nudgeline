"""Workflows, runs (one per order or event) and attempts (one per call or message)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base, TenantMixin, TimestampMixin


class Workflow(Base, TimestampMixin, TenantMixin):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    template_key: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="draft", nullable=False)  # draft|active|paused
    default_language: Mapped[str] = mapped_column(sa.String(4), server_default="auto", nullable=False)
    script: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class WorkflowRun(Base, TimestampMixin, TenantMixin):
    """One trigger (an order) moving through the workflow. Contact details are encrypted."""

    __tablename__ = "workflow_runs"
    __table_args__ = (
        sa.UniqueConstraint("tenant_id", "workflow_id", "external_ref", name="uq_runs_workflow_ref"),
        sa.Index("ix_runs_tenant_created", "tenant_id", "created_at"),
        sa.Index("ix_runs_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # shopify|webhook|test
    external_ref: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    order_number: Mapped[str] = mapped_column(sa.String(60), server_default="", nullable=False)
    contact_enc: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    phone_hash: Mapped[bytes] = mapped_column(sa.LargeBinary, nullable=False)
    phone_last4: Mapped[str] = mapped_column(sa.String(4), nullable=False)
    phone_country: Mapped[str | None] = mapped_column(sa.String(2))
    contact_timezone: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    language: Mapped[str] = mapped_column(sa.String(4), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), server_default="queued", nullable=False)
    status_reason: Mapped[str | None] = mapped_column(sa.String(60))
    outcome_channel: Mapped[str | None] = mapped_column(sa.String(20))
    outcome_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    call_attempts: Mapped[int] = mapped_column(sa.Integer, server_default="0", nullable=False)
    whatsapp_sent_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    next_action_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    compliance_log: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default="[]", nullable=False)
    actions_status: Mapped[str | None] = mapped_column(sa.String(20))  # pending|done|failed|skipped
    actions_error: Mapped[str | None] = mapped_column(sa.Text)


class RunAttempt(Base, TenantMixin):
    """One call or WhatsApp message for a run."""

    __tablename__ = "run_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # voice|whatsapp
    attempt_no: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    digit: Mapped[str | None] = mapped_column(sa.String(4))
    provider_ref: Mapped[str | None] = mapped_column(sa.String(120))
    duration_seconds: Mapped[int | None] = mapped_column(sa.Integer)
    cost: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 4))
    currency: Mapped[str | None] = mapped_column(sa.String(3))
    error: Mapped[str | None] = mapped_column(sa.Text)
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
