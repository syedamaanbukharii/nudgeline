"""Postgres-backed job queue: enqueue inside the caller's transaction, claim with SKIP LOCKED."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update

from modules.tenancy.domain.models import Job

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

STALE_LOCK = timedelta(minutes=10)


@dataclass(frozen=True)
class ClaimedJob:
    id: uuid.UUID
    tenant_id: uuid.UUID
    kind: str
    payload: dict[str, Any]
    attempts: int
    max_attempts: int


def enqueue(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    kind: str,
    payload: dict[str, Any],
    due_at: datetime | None = None,
    max_attempts: int = 5,
) -> Job:
    """Add a job in the current transaction, so it only exists if the caller commits."""
    job = Job(
        tenant_id=tenant_id,
        kind=kind,
        payload=payload,
        due_at=due_at or datetime.now(UTC),
        max_attempts=max_attempts,
    )
    session.add(job)
    return job


async def claim_due(session: AsyncSession, worker_id: str, limit: int) -> list[ClaimedJob]:
    """Lock up to `limit` due jobs for this worker. Call with a system session."""
    now = datetime.now(UTC)
    await session.execute(
        update(Job)
        .where(Job.status == "running", Job.locked_at < now - STALE_LOCK)
        .values(status="pending", locked_at=None, locked_by=None)
    )
    rows = (
        (
            await session.execute(
                select(Job)
                .where(Job.status == "pending", Job.due_at <= now)
                .order_by(Job.due_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        )
        .scalars()
        .all()
    )
    claimed = []
    for job in rows:
        job.status = "running"
        job.locked_at = now
        job.locked_by = worker_id
        job.attempts += 1
        claimed.append(ClaimedJob(job.id, job.tenant_id, job.kind, dict(job.payload), job.attempts, job.max_attempts))
    return claimed


async def mark_done(session: AsyncSession, job_id: uuid.UUID) -> None:
    await session.execute(
        update(Job).where(Job.id == job_id).values(status="done", completed_at=datetime.now(UTC), last_error=None)
    )


async def mark_failed(session: AsyncSession, job: ClaimedJob, error: str) -> None:
    """Retry with exponential backoff, or give up after max_attempts."""
    if job.attempts >= job.max_attempts:
        values: dict[str, Any] = {"status": "failed", "completed_at": datetime.now(UTC)}
    else:
        backoff = timedelta(seconds=min(30 * 2 ** (job.attempts - 1), 3600))
        values = {"status": "pending", "due_at": datetime.now(UTC) + backoff, "locked_at": None, "locked_by": None}
    await session.execute(update(Job).where(Job.id == job.id).values(last_error=error[:2000], **values))
