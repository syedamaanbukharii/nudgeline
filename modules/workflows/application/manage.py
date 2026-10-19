"""Workflow CRUD, run queries and dashboard stats."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError
from sqlalchemy import ColumnElement, func, or_, select

from modules.tenancy.application.audit import audit
from modules.tenancy.application.keyring import tenant_data_key
from modules.tenancy.domain.crypto import decrypt_json
from modules.workflows.application.ingest import IngestResult, OrderEvent, ingest_order
from modules.workflows.domain.models import RunAttempt, Workflow, WorkflowRun
from modules.workflows.domain.settings import Script, WorkflowSettings
from modules.workflows.domain.templates import get_template

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from modules.tenancy.domain.models import Tenant


class WorkflowError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _validated(script: dict[str, Any], settings: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        return Script.model_validate(script).model_dump(), WorkflowSettings.model_validate(settings).model_dump()
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"])
        raise WorkflowError(422, f"{where}: {first['msg']}" if where else first["msg"]) from exc


async def list_workflows(session: AsyncSession) -> list[Workflow]:
    return list((await session.execute(select(Workflow).order_by(Workflow.created_at.desc()))).scalars())


async def get_workflow(session: AsyncSession, workflow_id: uuid.UUID) -> Workflow:
    workflow = await session.get(Workflow, workflow_id)
    if workflow is None:
        raise WorkflowError(404, "Workflow not found")
    return workflow


async def create_workflow(
    session: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, *, template_key: str, name: str | None
) -> Workflow:
    try:
        template = get_template(template_key)
    except KeyError as exc:
        raise WorkflowError(422, "Unknown or unavailable template") from exc
    script, settings = _validated(template.script, {})
    base = (name or template.name["en"]).strip()[:110]
    taken = set((await session.execute(select(Workflow.name))).scalars())
    unique, n = base, 2
    while unique in taken:
        unique, n = f"{base} {n}", n + 1
    workflow = Workflow(
        tenant_id=tenant_id,
        name=unique,
        template_key=template.key,
        status="draft",
        default_language="auto",
        script=script,
        settings=settings,
        created_by=user_id,
    )
    session.add(workflow)
    await session.flush()
    audit(session, tenant_id, user_id, "workflow.created", "workflow", workflow.id, {"template": template.key})
    return workflow


async def update_workflow(
    session: AsyncSession,
    user_id: uuid.UUID,
    workflow_id: uuid.UUID,
    *,
    name: str | None = None,
    default_language: str | None = None,
    script: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
) -> Workflow:
    workflow = await get_workflow(session, workflow_id)
    new_script, new_settings = _validated(script or workflow.script, settings or workflow.settings)
    if default_language is not None:
        if default_language not in ("auto", "ar", "en"):
            raise WorkflowError(422, "default_language must be auto, ar or en")
        workflow.default_language = default_language
    if name is not None:
        workflow.name = name.strip()[:120] or workflow.name
    workflow.script, workflow.settings = new_script, new_settings
    audit(session, workflow.tenant_id, user_id, "workflow.updated", "workflow", workflow.id)
    return workflow


async def set_status(session: AsyncSession, user_id: uuid.UUID, workflow_id: uuid.UUID, status: str) -> Workflow:
    # Several workflows can be active; each order goes to the oldest active one whose trigger matches.
    workflow = await get_workflow(session, workflow_id)
    workflow.status = status
    audit(session, workflow.tenant_id, user_id, f"workflow.{status}", "workflow", workflow.id)
    return workflow


async def test_run(
    session: AsyncSession,
    tenant: Tenant,
    workflow_id: uuid.UUID,
    *,
    phone: str,
    customer_name: str,
    language: str | None,
) -> IngestResult:
    """Run the workflow once against your own phone, as if an order had arrived."""
    workflow = await get_workflow(session, workflow_id)
    ref = uuid.uuid4().hex[:12]
    event = OrderEvent(
        source="test",
        external_ref=f"test-{ref}",
        customer_name=customer_name,
        phone=phone,
        order_number=f"TEST-{ref[:6].upper()}",
        locale=language,
        total="149",
        currency=tenant.currency,
        items=[{"name": "Test item", "quantity": 1}],
    )
    return await ingest_order(session, tenant, event, workflow=workflow)


# ── Runs ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RunView:
    run: WorkflowRun
    customer_name: str
    phone_masked: str
    attempts: list[RunAttempt]


NEEDS_ATTENTION = ("no_response", "failed")


def mask_phone(phone: str) -> str:
    return phone[:4] + "•" * max(len(phone) - 8, 2) + phone[-4:] if len(phone) > 8 else "••" + phone[-4:]


async def list_runs(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    status: str | None = None,
    workflow_id: uuid.UUID | None = None,
    before: datetime | None = None,
    search: str | None = None,
    limit: int = 50,
) -> list[RunView]:
    query = select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(min(limit, 200))
    if status == "attention":
        query = query.where(WorkflowRun.status.in_(NEEDS_ATTENTION))
    elif status:
        query = query.where(WorkflowRun.status == status)
    if search and (term := search.strip()):
        # Names and phone numbers are encrypted, so search covers order numbers and the phone's last 4 digits.
        like = f"%{term.lstrip('#')}%"
        conditions: list[ColumnElement[bool]] = [
            WorkflowRun.order_number.ilike(like),
            WorkflowRun.external_ref.ilike(like),
        ]
        if term.isdigit() and len(term) == 4:
            conditions.append(WorkflowRun.phone_last4 == term)
        query = query.where(or_(*conditions))
    if workflow_id:
        query = query.where(WorkflowRun.workflow_id == workflow_id)
    if before:
        query = query.where(WorkflowRun.created_at < before)
    runs = list((await session.execute(query)).scalars())
    key = await tenant_data_key(session, tenant_id)
    views = []
    for run in runs:
        contact = decrypt_json(run.contact_enc, key)
        views.append(RunView(run, str(contact.get("name", "")), mask_phone(str(contact.get("phone", ""))), []))
    return views


async def get_run(session: AsyncSession, tenant_id: uuid.UUID, run_id: uuid.UUID) -> RunView:
    run = await session.get(WorkflowRun, run_id)
    if run is None:
        raise WorkflowError(404, "Run not found")
    attempts = list(
        (
            await session.execute(select(RunAttempt).where(RunAttempt.run_id == run.id).order_by(RunAttempt.started_at))
        ).scalars()
    )
    contact = decrypt_json(run.contact_enc, await tenant_data_key(session, tenant_id))
    return RunView(run, str(contact.get("name", "")), mask_phone(str(contact.get("phone", ""))), attempts)


async def reveal_phone(session: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, run_id: uuid.UUID) -> str:
    """Full number for an agent who needs to call the customer by hand. Every reveal is audited."""
    run = await session.get(WorkflowRun, run_id)
    if run is None:
        raise WorkflowError(404, "Run not found")
    contact = decrypt_json(run.contact_enc, await tenant_data_key(session, tenant_id))
    audit(session, tenant_id, user_id, "run.phone_revealed", "run", run.id)
    return str(contact.get("phone", ""))


async def overview(session: AsyncSession, *, days: int, avg_return_cost: float) -> dict[str, Any]:
    since = datetime.now(UTC) - timedelta(days=days)
    counts = dict(
        (
            await session.execute(
                select(WorkflowRun.status, func.count())
                .where(WorkflowRun.created_at >= since, WorkflowRun.source != "test")
                .group_by(WorkflowRun.status)
            )
        ).all()
    )
    daily = (
        await session.execute(
            select(func.date_trunc("day", WorkflowRun.created_at).label("day"), WorkflowRun.status, func.count())
            .where(WorkflowRun.created_at >= since, WorkflowRun.source != "test")
            .group_by("day", WorkflowRun.status)
            .order_by("day")
        )
    ).all()
    minutes = (
        await session.execute(
            select(func.coalesce(func.sum(RunAttempt.duration_seconds), 0)).where(
                RunAttempt.channel == "voice", RunAttempt.started_at >= since
            )
        )
    ).scalar_one()
    total = sum(counts.values())
    confirmed, cancelled = counts.get("confirmed", 0), counts.get("cancelled", 0)
    answered = confirmed + cancelled
    series: dict[str, dict[str, int]] = {}
    for day, status, n in daily:
        series.setdefault(day.date().isoformat(), {})[status] = n
    return {
        "days": days,
        "total": total,
        "needs_attention": sum(counts.get(s, 0) for s in NEEDS_ATTENTION),
        "by_status": counts,
        "confirmation_rate": round(confirmed / answered, 3) if answered else None,
        "response_rate": round(answered / total, 3) if total else None,
        # Every cancellation caught before dispatch is a delivery that would have come back.
        "estimated_savings": round(cancelled * avg_return_cost, 2),
        "call_minutes": round(int(minutes or 0) / 60, 1),
        "series": [{"day": d, **s} for d, s in series.items()],
    }
