"""Moves runs through their workflow. Called by the worker for each due job."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Protocol

import structlog
from sqlalchemy import select

from modules.compliance.application import dnc
from modules.tenancy.application.jobs import enqueue
from modules.tenancy.application.keyring import tenant_data_key
from modules.tenancy.domain.crypto import decrypt_json
from modules.tenancy.domain.models import Tenant
from modules.workflows.application.ingest import ACTIONS_JOB, STEP_JOB
from modules.workflows.domain.flow import (
    TERMINAL,
    RunState,
    Step,
    after_failed_call,
    currency_words,
    next_step,
    render,
    spoken_amount,
)
from modules.workflows.domain.models import RunAttempt, Workflow, WorkflowRun
from modules.workflows.domain.settings import Script, WorkflowSettings
from modules.workflows.domain.templates import get_template
from modules.workflows.ports.channels import CallRequest, CallResult, Channels, OutcomeEvent, WhatsAppRequest

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

PAUSED_RECHECK = timedelta(minutes=10)
STALE_CALL = timedelta(minutes=10)


class ChannelProvider(Protocol):
    async def for_tenant(self, session: AsyncSession, tenant_id: uuid.UUID) -> Channels: ...


@dataclass(frozen=True)
class _CallPlan:
    request: CallRequest
    attempt_id: uuid.UUID
    attempt_no: int
    settings: WorkflowSettings
    digits: dict[str, str]


def _variables(run: WorkflowRun, contact: dict[str, Any], store_name: str) -> dict[str, str]:
    payload = run.payload or {}
    items = payload.get("items") or []
    return {
        "customer_name": str(contact.get("name") or "").split(" ")[0],
        "store_name": store_name,
        "order_number": run.order_number,
        "total": spoken_amount(payload.get("total")),
        "currency": currency_words(payload.get("currency"), run.language),
        "items": str(sum(int(i.get("quantity") or 1) for i in items)) if items else "",
    }


class WorkflowEngine:
    def __init__(
        self,
        session_scope: Callable[[uuid.UUID], AbstractAsyncContextManager[AsyncSession]],
        channels: ChannelProvider,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._scope = session_scope
        self._channels = channels
        self._now = clock

    # ── Job: run.step ──────────────────────────────────────────────

    async def step(self, tenant_id: uuid.UUID, run_id: uuid.UUID) -> None:
        plan = await self._decide_and_prepare(tenant_id, run_id)
        if plan is None:
            return
        async with self._scope(tenant_id) as session:
            telephony = (await self._channels.for_tenant(session, tenant_id)).telephony
        result = CallResult("failed", error="telephony_not_configured")
        if telephony is not None:
            try:
                result = await telephony.place_keypad_call(plan.request)
            except Exception as exc:  # the call is over either way; record it and retry later
                logger.exception("call.failed", run_id=str(run_id))
                result = CallResult("failed", error=str(exc)[:500])
        await self._record_call(tenant_id, run_id, plan, result)

    async def _decide_and_prepare(self, tenant_id: uuid.UUID, run_id: uuid.UUID) -> _CallPlan | None:
        """Everything before dialing, in one transaction. Returns a plan when a call should be placed."""
        now = self._now()
        async with self._scope(tenant_id) as session:
            run = (
                await session.execute(select(WorkflowRun).where(WorkflowRun.id == run_id).with_for_update())
            ).scalar_one_or_none()
            if run is None or run.status in TERMINAL:
                return None
            if run.status == "in_progress" and run.updated_at > now - STALE_CALL:
                return None
            workflow = await session.get(Workflow, run.workflow_id)
            if workflow is None:
                return None
            if workflow.status != "active":
                run.status, run.status_reason = "waiting", "workflow_paused"
                run.next_action_at = now + PAUSED_RECHECK
                enqueue(session, tenant_id, STEP_JOB, {"run_id": str(run.id)}, due_at=run.next_action_at)
                return None

            settings = WorkflowSettings.model_validate(workflow.settings)
            channels = await self._channels.for_tenant(session, tenant_id)
            data_key = await tenant_data_key(session, tenant_id)
            contact = decrypt_json(run.contact_enc, data_key)
            phone = str(contact["phone"])

            step = next_step(
                RunState(
                    whatsapp_sent_at=run.whatsapp_sent_at,
                    call_attempts=run.call_attempts,
                    on_dnc_list=await dnc.is_blocked(session, tenant_id, phone),
                    contact_timezone=run.contact_timezone,
                ),
                settings,
                now,
                whatsapp_available=channels.whatsapp is not None,
                telephony_available=channels.telephony is not None,
            )
            if step.decision is not None:
                run.compliance_log = [*run.compliance_log, step.decision.as_dict()]

            tenant = await session.get(Tenant, tenant_id)
            store_name = tenant.name if tenant else ""
            variables = _variables(run, contact, store_name)

            if step.kind == "send_whatsapp" and channels.whatsapp is not None:
                await self._send_whatsapp(session, run, settings, phone, variables, channels, now)
                return None
            if step.kind == "wait":
                self._wait(session, run, step)
                return None
            if step.kind == "finish":
                self._finish(session, run, step.outcome or "failed", step.reason, channel=None, now=now)
                return None

            # place_call
            template = get_template(workflow.template_key)
            script = getattr(Script.model_validate(workflow.script), run.language)
            digits = {o.digit: o.outcome for o in template.options}
            run.call_attempts += 1
            run.status, run.status_reason = "in_progress", "calling"
            attempt = RunAttempt(
                tenant_id=tenant_id, run_id=run.id, channel="voice", attempt_no=run.call_attempts, status="dialing"
            )
            session.add(attempt)
            await session.flush()
            request = CallRequest(
                run_id=run.id,
                to=phone,
                language=run.language,
                prompt=render(script.prompt, variables),
                replies={
                    "confirmed": render(script.confirmed, variables),
                    "cancelled": render(script.cancelled, variables),
                    "no_input": render(script.no_input, variables),
                },
                digits=digits,
                repeat_prompt=settings.call.repeat_prompt,
                input_timeout_seconds=settings.call.input_timeout_seconds,
            )
            return _CallPlan(request, attempt.id, run.call_attempts, settings, digits)

    async def _send_whatsapp(
        self,
        session: AsyncSession,
        run: WorkflowRun,
        settings: WorkflowSettings,
        phone: str,
        variables: dict[str, str],
        channels: Channels,
        now: datetime,
    ) -> None:
        assert channels.whatsapp is not None
        attempt = RunAttempt(tenant_id=run.tenant_id, run_id=run.id, channel="whatsapp", attempt_no=1, status="sent")
        try:
            attempt.provider_ref = await channels.whatsapp.send_template(
                WhatsAppRequest(
                    run_id=run.id,
                    to=phone,
                    language=run.language,
                    template_name=settings.whatsapp.template_name,
                    parameters=[
                        variables["customer_name"],
                        variables["order_number"],
                        f"{variables['total']} {variables['currency']}".strip(),
                    ],
                    button_payloads=[f"{run.id}:1", f"{run.id}:2"],
                )
            )
        except Exception as exc:
            logger.warning("whatsapp.send_failed", run_id=str(run.id), error=str(exc)[:200])
            attempt.status, attempt.error = "failed", str(exc)[:500]
        attempt.ended_at = now
        session.add(attempt)
        # A failed send still counts as "sent" so the flow falls through to the call instead of looping.
        run.whatsapp_sent_at = now
        wait_until = now + timedelta(minutes=settings.whatsapp.wait_minutes)
        if attempt.status == "failed":
            wait_until = now
        self._wait(session, run, Step("wait", until=wait_until, reason="awaiting_whatsapp_reply"))

    async def _record_call(
        self,
        tenant_id: uuid.UUID,
        run_id: uuid.UUID,
        plan: _CallPlan,
        result: CallResult,
    ) -> None:
        now = self._now()
        status, digit = result.status, result.digit
        async with self._scope(tenant_id) as session:
            run = (
                await session.execute(select(WorkflowRun).where(WorkflowRun.id == run_id).with_for_update())
            ).scalar_one()
            attempt = await session.get(RunAttempt, plan.attempt_id)
            if attempt is not None:
                attempt.status, attempt.digit, attempt.duration_seconds = status, digit, result.duration_seconds
                attempt.provider_ref, attempt.error, attempt.ended_at = result.provider_ref, result.error, now
            if run.status in TERMINAL:  # e.g. the customer replied on WhatsApp during the call
                return
            outcome = plan.digits.get(digit or "") if status == "answered" else None
            if outcome:
                self._finish(session, run, outcome, f"pressed_{digit}", channel="voice", now=now)
                return
            step = after_failed_call(plan.attempt_no, plan.settings, now)
            if step.kind == "finish":
                self._finish(session, run, step.outcome or "no_response", step.reason, channel=None, now=now)
            else:
                self._wait(session, run, Step("wait", until=step.until, reason=f"call_{status}"))

    # ── Replies arriving on other channels ─────────────────────────

    async def record_reply(self, tenant_id: uuid.UUID, run_id: uuid.UUID, digit: str, channel: str) -> str | None:
        """A customer answered outside a call (a WhatsApp button). Returns the outcome, if any."""
        now = self._now()
        async with self._scope(tenant_id) as session:
            run = (
                await session.execute(select(WorkflowRun).where(WorkflowRun.id == run_id).with_for_update())
            ).scalar_one_or_none()
            if run is None or run.status in TERMINAL:
                return None
            workflow = await session.get(Workflow, run.workflow_id)
            if workflow is None:
                return None
            outcome = get_template(workflow.template_key).outcome_for_digit(digit)
            if outcome is None:
                return None
            session.add(
                RunAttempt(
                    tenant_id=tenant_id,
                    run_id=run.id,
                    channel=channel,
                    attempt_no=1,
                    status="replied",
                    digit=digit,
                    ended_at=now,
                )
            )
            self._finish(session, run, outcome, f"{channel}_reply", channel=channel, now=now)
            return outcome

    # ── Manual controls ────────────────────────────────────────────

    async def retry(self, session: AsyncSession, run: WorkflowRun) -> None:
        """Give a finished or stuck run a fresh round of attempts (used from the dashboard)."""
        now = self._now()
        run.status, run.status_reason = "queued", "manual_retry"
        run.call_attempts, run.whatsapp_sent_at, run.outcome_at, run.outcome_channel = 0, None, None, None
        run.actions_status, run.actions_error, run.next_action_at = None, None, now
        enqueue(session, run.tenant_id, STEP_JOB, {"run_id": str(run.id)}, due_at=now)

    async def cancel(self, session: AsyncSession, run: WorkflowRun) -> None:
        """Stop contacting this customer. No store action is taken."""
        run.status, run.status_reason, run.outcome_at = "skipped", "stopped_by_user", self._now()
        run.next_action_at = None

    # ── Job: run.actions ───────────────────────────────────────────

    async def apply_actions(self, tenant_id: uuid.UUID, run_id: uuid.UUID) -> None:
        async with self._scope(tenant_id) as session:
            run = await session.get(WorkflowRun, run_id)
            if run is None or run.actions_status == "done":
                return
            workflow = await session.get(Workflow, run.workflow_id)
            channels = await self._channels.for_tenant(session, tenant_id)
            sink = channels.outcome_sinks.get(run.source)
            if workflow is None or sink is None or run.status not in ("confirmed", "cancelled", "no_response"):
                run.actions_status = "skipped"
                return
            action = getattr(WorkflowSettings.model_validate(workflow.settings).actions, run.status)
            event = OutcomeEvent(
                run_id=run.id,
                source=run.source,
                external_ref=run.external_ref,
                order_number=run.order_number,
                outcome=run.status,
                channel=run.outcome_channel,
                tag=action.tag,
                cancel_order=action.cancel_order,
            )
        try:
            await sink.apply(event)
        except Exception as exc:
            async with self._scope(tenant_id) as session:
                run = await session.get(WorkflowRun, run_id)
                if run is not None:
                    run.actions_status, run.actions_error = "failed", str(exc)[:1000]
            raise
        async with self._scope(tenant_id) as session:
            run = await session.get(WorkflowRun, run_id)
            if run is not None:
                run.actions_status, run.actions_error = "done", None

    # ── Helpers ────────────────────────────────────────────────────

    def _wait(self, session: AsyncSession, run: WorkflowRun, step: Step) -> None:
        until = step.until or self._now()
        run.status, run.status_reason, run.next_action_at = "waiting", step.reason, until
        enqueue(session, run.tenant_id, STEP_JOB, {"run_id": str(run.id)}, due_at=until)

    def _finish(
        self,
        session: AsyncSession,
        run: WorkflowRun,
        outcome: str,
        reason: str | None,
        *,
        channel: str | None,
        now: datetime,
    ) -> None:
        run.status, run.status_reason = outcome, reason
        run.outcome_channel, run.outcome_at, run.next_action_at = channel, now, None
        if outcome in ("confirmed", "cancelled", "no_response"):
            run.actions_status = "pending"
            enqueue(session, run.tenant_id, ACTIONS_JOB, {"run_id": str(run.id)}, max_attempts=8)
        logger.info("run.finished", run_id=str(run.id), outcome=outcome, reason=reason)
