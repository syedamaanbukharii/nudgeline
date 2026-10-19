"""Turn an incoming order into a workflow run."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import phonenumbers
from phonenumbers import timezone as phone_timezone
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from modules.tenancy.application.jobs import enqueue
from modules.tenancy.application.keyring import phone_hash, tenant_data_key
from modules.tenancy.domain.crypto import encrypt_json
from modules.workflows.domain.flow import choose_language
from modules.workflows.domain.models import Workflow, WorkflowRun
from modules.workflows.domain.settings import WorkflowSettings
from modules.workflows.domain.templates import TEMPLATES

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.tenancy.domain.models import Tenant

STEP_JOB = "run.step"
ACTIONS_JOB = "run.actions"


@dataclass(frozen=True)
class OrderEvent:
    source: str
    external_ref: str
    customer_name: str
    phone: str
    order_number: str = ""
    locale: str | None = None
    total: str | None = None
    currency: str | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
    payment_type: str = "unknown"  # cod | prepaid | unknown
    is_first_order: bool | None = None


@dataclass(frozen=True)
class IngestResult:
    status: str  # created | duplicate | ignored
    run_id: uuid.UUID | None = None
    reason: str | None = None


@dataclass(frozen=True)
class NormalizedPhone:
    e164: str
    country: str | None
    timezone: str
    valid: bool


def normalize_phone(raw: str, default_country: str, fallback_timezone: str) -> NormalizedPhone:
    try:
        number = phonenumbers.parse(raw, default_country)
    except phonenumbers.NumberParseException:
        digits = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
        return NormalizedPhone(digits or raw, None, fallback_timezone, False)
    e164 = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    zones = [z for z in phone_timezone.time_zones_for_number(number) if z != "Etc/Unknown"]
    return NormalizedPhone(
        e164=e164,
        country=phonenumbers.region_code_for_number(number),
        timezone=zones[0] if zones else fallback_timezone,
        valid=phonenumbers.is_valid_number(number),
    )


async def active_workflows(session: AsyncSession) -> list[Workflow]:
    ecommerce = [k for k, t in TEMPLATES.items() if t.industry == "ecommerce"]
    return list(
        (
            await session.execute(
                select(Workflow)
                .where(Workflow.status == "active", Workflow.template_key.in_(ecommerce))
                .order_by(Workflow.created_at)
            )
        ).scalars()
    )


async def route(session: AsyncSession, event: OrderEvent) -> tuple[Workflow | None, str | None]:
    """The first active workflow whose trigger accepts this order, or the reason none did."""
    workflows = await active_workflows(session)
    if not workflows:
        return None, "no_active_workflow"
    reasons = []
    for workflow in workflows:
        trigger = WorkflowSettings.model_validate(workflow.settings).trigger
        reason = trigger.matches(event.payment_type, event.total, event.is_first_order)
        if reason is None:
            return workflow, None
        reasons.append(reason)
    return None, reasons[0] if len(set(reasons)) == 1 else "no_matching_workflow"


async def ingest_order(
    session: AsyncSession,
    tenant: Tenant,
    event: OrderEvent,
    workflow: Workflow | None = None,
    now: datetime | None = None,
) -> IngestResult:
    """Create a run for an order (idempotent on the order's external reference)."""
    now = now or datetime.now(UTC)
    existing = (
        await session.execute(
            select(WorkflowRun.id).where(
                WorkflowRun.source == event.source, WorkflowRun.external_ref == event.external_ref[:120]
            )
        )
    ).scalar_one_or_none()
    if existing is not None:  # the same order delivered twice (webhook retries)
        return IngestResult("duplicate", run_id=existing)
    if workflow is None:
        workflow, skip_reason = await route(session, event)
        if workflow is None:
            return IngestResult("ignored", reason=skip_reason)
    settings = WorkflowSettings.model_validate(workflow.settings)

    phone = normalize_phone(event.phone, tenant.country, tenant.timezone)
    data_key = await tenant_data_key(session, tenant.id)
    status, reason = ("queued", None) if phone.valid else ("failed", "invalid_phone")

    run_id = uuid.uuid4()
    inserted = (
        await session.execute(
            insert(WorkflowRun)
            .values(
                id=run_id,
                tenant_id=tenant.id,
                workflow_id=workflow.id,
                source=event.source,
                external_ref=event.external_ref[:120],
                order_number=event.order_number[:60],
                contact_enc=encrypt_json({"name": event.customer_name, "phone": phone.e164}, data_key),
                phone_hash=phone_hash(phone.e164, tenant.id),
                phone_last4=phone.e164[-4:],
                phone_country=phone.country,
                contact_timezone=phone.timezone,
                language=choose_language(event.locale, workflow.default_language, phone.country),
                payload={
                    "total": event.total,
                    "currency": event.currency or tenant.currency,
                    "items": event.items[:50],
                    "locale": event.locale,
                },
                status=status,
                status_reason=reason,
                next_action_at=now + timedelta(minutes=settings.delay_minutes) if phone.valid else None,
            )
            .on_conflict_do_nothing(constraint="uq_runs_workflow_ref")
            .returning(WorkflowRun.id)
        )
    ).scalar_one_or_none()

    if inserted is None:
        existing = (
            await session.execute(
                select(WorkflowRun.id).where(
                    WorkflowRun.workflow_id == workflow.id, WorkflowRun.external_ref == event.external_ref[:120]
                )
            )
        ).scalar_one()
        return IngestResult("duplicate", run_id=existing)

    if phone.valid:
        enqueue(
            session,
            tenant.id,
            STEP_JOB,
            {"run_id": str(run_id)},
            due_at=now + timedelta(minutes=settings.delay_minutes),
        )
    return IngestResult("created", run_id=run_id, reason=reason)
