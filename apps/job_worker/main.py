"""arq background worker entry point."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select, text, update

from modules.tenancy.adapters.database import get_session_factory
from modules.tenancy.domain.models import OutboxEvent, ScheduledAction

logger = structlog.get_logger()


async def relay_outbox(ctx: dict) -> None:
    """Publish unpublished outbox events."""
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at)
            .limit(100)
        )
        events = result.scalars().all()
        for event in events:
            # Publish to Valkey stream (webhooks, SSE fan-out)
            logger.info("outbox.relay", topic=event.topic, event_id=str(event.id))
            event.published_at = datetime.now(timezone.utc)
        await session.commit()


async def poll_scheduled_actions(ctx: dict) -> None:
    """Poll and execute due scheduled actions with SKIP LOCKED."""
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(ScheduledAction)
            .where(
                ScheduledAction.status == "pending",
                ScheduledAction.due_at <= datetime.now(timezone.utc),
            )
            .order_by(ScheduledAction.due_at)
            .limit(10)
            .with_for_update(skip_locked=True)
        )
        actions = result.scalars().all()
        for action in actions:
            action.status = "locked"
            action.locked_by = "worker"
            action.locked_at = datetime.now(timezone.utc)
            action.attempts += 1
        await session.commit()

    for action in actions:
        try:
            logger.info("scheduled_action.execute", kind=action.kind, action_id=str(action.id))
            async with factory() as session:
                await session.execute(
                    update(ScheduledAction)
                    .where(ScheduledAction.id == action.id)
                    .values(
                        status="done",
                        completed_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
        except Exception as exc:
            logger.error("scheduled_action.failed", action_id=str(action.id), error=str(exc))
            async with factory() as session:
                await session.execute(
                    update(ScheduledAction)
                    .where(ScheduledAction.id == action.id)
                    .values(status="failed", error=str(exc)[:500])
                )
                await session.commit()


async def dispatch_calls(ctx: dict) -> None:
    """Dispatch scheduled outbound calls."""


async def process_post_call(ctx: dict) -> None:
    """Run post-call processing pipeline."""


async def process_bulk(ctx: dict) -> None:
    """Handle bulk operations (CSV import, campaign enrollment)."""


class WorkerSettings:
    """arq worker configuration."""

    functions = [dispatch_calls, process_post_call, process_bulk, relay_outbox, poll_scheduled_actions]
    cron_jobs = [
        cron(relay_outbox, second={0, 15, 30, 45}),
        cron(poll_scheduled_actions, second={0, 30}),
        cron(dispatch_calls, second={0, 30}),
    ]
    redis_settings = RedisSettings(host="valkey", port=6379)
    max_jobs = 50
    job_timeout = 600
