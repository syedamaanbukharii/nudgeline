"""Templates, workflows, runs and the overview dashboard."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from apps.api.dependencies import Context, require
from apps.wiring import build_engine
from modules.integrations.domain.models import Integration
from modules.workflows.application import manage
from modules.workflows.domain.models import Workflow, WorkflowRun
from modules.workflows.domain.templates import TEMPLATES

router = APIRouter(prefix="/v1", tags=["workflows"])

ViewWorkflows = Annotated[Context, Depends(require("workflows.view"))]
ManageWorkflows = Annotated[Context, Depends(require("workflows.manage"))]
ViewRuns = Annotated[Context, Depends(require("runs.view"))]
ManageRuns = Annotated[Context, Depends(require("runs.manage"))]


def _workflow(w: Workflow) -> dict[str, Any]:
    return {
        "id": str(w.id),
        "name": w.name,
        "template_key": w.template_key,
        "status": w.status,
        "default_language": w.default_language,
        "script": w.script,
        "settings": w.settings,
        "created_at": w.created_at,
        "updated_at": w.updated_at,
    }


def _run(view: manage.RunView, detail: bool = False) -> dict[str, Any]:
    r = view.run
    item: dict[str, Any] = {
        "id": str(r.id),
        "workflow_id": str(r.workflow_id),
        "source": r.source,
        "external_ref": r.external_ref,
        "order_number": r.order_number,
        "customer_name": view.customer_name,
        "phone": view.phone_masked,
        "language": r.language,
        "status": r.status,
        "status_reason": r.status_reason,
        "outcome_channel": r.outcome_channel,
        "call_attempts": r.call_attempts,
        "total": (r.payload or {}).get("total"),
        "currency": (r.payload or {}).get("currency"),
        "next_action_at": r.next_action_at,
        "outcome_at": r.outcome_at,
        "actions_status": r.actions_status,
        "created_at": r.created_at,
    }
    if detail:
        item["items"] = (r.payload or {}).get("items", [])
        item["contact_timezone"] = r.contact_timezone
        item["compliance_log"] = r.compliance_log
        item["actions_error"] = r.actions_error
        item["attempts"] = [
            {
                "id": str(a.id),
                "channel": a.channel,
                "attempt_no": a.attempt_no,
                "status": a.status,
                "digit": a.digit,
                "duration_seconds": a.duration_seconds,
                "error": a.error,
                "started_at": a.started_at,
                "ended_at": a.ended_at,
            }
            for a in view.attempts
        ]
    return item


@router.get("/templates")
async def templates(ctx: ViewWorkflows) -> list[dict[str, Any]]:
    return [t.as_dict() for t in TEMPLATES.values()]


class WorkflowIn(BaseModel):
    template_key: str
    name: str | None = Field(default=None, max_length=120)


class WorkflowPatch(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    default_language: str | None = None
    script: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None


class TestCallIn(BaseModel):
    phone: str = Field(min_length=6, max_length=32)
    customer_name: str = Field(default="Test", max_length=80)
    language: str | None = Field(default=None, pattern="^(ar|en)$")


@router.get("/workflows")
async def list_workflows(ctx: ViewWorkflows) -> list[dict[str, Any]]:
    return [_workflow(w) for w in await manage.list_workflows(ctx.session)]


@router.post("/workflows", status_code=201)
async def create_workflow(body: WorkflowIn, ctx: ManageWorkflows) -> dict[str, Any]:
    w = await manage.create_workflow(
        ctx.session, ctx.tenant_id, ctx.user_id, template_key=body.template_key, name=body.name
    )
    return _workflow(w)


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: uuid.UUID, ctx: ViewWorkflows) -> dict[str, Any]:
    return _workflow(await manage.get_workflow(ctx.session, workflow_id))


@router.patch("/workflows/{workflow_id}")
async def update_workflow(workflow_id: uuid.UUID, body: WorkflowPatch, ctx: ManageWorkflows) -> dict[str, Any]:
    w = await manage.update_workflow(ctx.session, ctx.user_id, workflow_id, **body.model_dump(exclude_none=True))
    return _workflow(w)


@router.post("/workflows/{workflow_id}/activate")
async def activate(workflow_id: uuid.UUID, ctx: ManageWorkflows) -> dict[str, Any]:
    return _workflow(await manage.set_status(ctx.session, ctx.user_id, workflow_id, "active"))


@router.post("/workflows/{workflow_id}/pause")
async def pause(workflow_id: uuid.UUID, ctx: ManageWorkflows) -> dict[str, Any]:
    return _workflow(await manage.set_status(ctx.session, ctx.user_id, workflow_id, "paused"))


@router.post("/workflows/{workflow_id}/test", status_code=202)
async def test_call(workflow_id: uuid.UUID, body: TestCallIn, ctx: ManageRuns) -> dict[str, Any]:
    result = await manage.test_run(
        ctx.session,
        ctx.principal.tenant,
        workflow_id,
        phone=body.phone,
        customer_name=body.customer_name,
        language=body.language,
    )
    return {"status": result.status, "run_id": str(result.run_id) if result.run_id else None, "reason": result.reason}


# ── Runs ───────────────────────────────────────────────────────────


@router.get("/runs")
async def list_runs(
    ctx: ViewRuns,
    status: str | None = None,
    workflow_id: uuid.UUID | None = None,
    before: datetime | None = None,
    q: Annotated[str | None, Query(max_length=60)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[dict[str, Any]]:
    views = await manage.list_runs(
        ctx.session, ctx.tenant_id, status=status, workflow_id=workflow_id, before=before, search=q, limit=limit
    )
    return [_run(v) for v in views]


@router.get("/runs/{run_id}")
async def get_run(run_id: uuid.UUID, ctx: ViewRuns) -> dict[str, Any]:
    return _run(await manage.get_run(ctx.session, ctx.tenant_id, run_id), detail=True)


@router.post("/runs/{run_id}/retry", status_code=202)
async def retry_run(run_id: uuid.UUID, ctx: ManageRuns) -> dict[str, Any]:
    view = await manage.get_run(ctx.session, ctx.tenant_id, run_id)
    if view.run.status == "in_progress":
        raise manage.WorkflowError(409, "A call is in progress")
    await build_engine().retry(ctx.session, view.run)
    return {"ok": True}


@router.post("/runs/{run_id}/reveal")
async def reveal_phone(run_id: uuid.UUID, ctx: ManageRuns) -> dict[str, str]:
    return {"phone": await manage.reveal_phone(ctx.session, ctx.tenant_id, ctx.user_id, run_id)}


@router.post("/runs/{run_id}/stop")
async def stop_run(run_id: uuid.UUID, ctx: ManageRuns) -> dict[str, Any]:
    view = await manage.get_run(ctx.session, ctx.tenant_id, run_id)
    await build_engine().cancel(ctx.session, view.run)
    return {"ok": True}


@router.get("/setup")
async def setup(ctx: ViewWorkflows) -> dict[str, bool]:
    """Onboarding checklist for a new account."""
    statuses = set((await ctx.session.execute(select(Workflow.status))).scalars())
    stores = (
        await ctx.session.execute(
            select(func.count()).select_from(Integration).where(Integration.provider.in_(("shopify", "webhook")))
        )
    ).scalar_one()
    tests = (
        await ctx.session.execute(select(func.count()).select_from(WorkflowRun).where(WorkflowRun.source == "test"))
    ).scalar_one()
    return {
        "workflow_created": bool(statuses),
        "store_connected": stores > 0,
        "test_call_placed": tests > 0,
        "workflow_active": "active" in statuses,
        "return_cost_set": bool(ctx.principal.tenant.settings.get("avg_return_cost")),
    }


@router.get("/overview")
async def overview(ctx: ViewRuns, days: Annotated[int, Query(ge=1, le=90)] = 7) -> dict[str, Any]:
    tenant = ctx.principal.tenant
    data = await manage.overview(
        ctx.session, days=days, avg_return_cost=float(tenant.settings.get("avg_return_cost", 0))
    )
    data["currency"] = tenant.currency
    return data
