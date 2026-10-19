"""Background worker: claims due jobs from Postgres and runs them through the workflow engine."""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import socket
import uuid
from typing import TYPE_CHECKING

import structlog

from apps.api.middleware.logging import configure_logging
from apps.wiring import build_engine
from modules.tenancy.adapters.database import dispose_engines, system_session
from modules.tenancy.application import jobs
from modules.tenancy.domain.settings import get_settings
from modules.workflows.application.ingest import ACTIONS_JOB, STEP_JOB

if TYPE_CHECKING:
    from modules.workflows.application.engine import WorkflowEngine

logger = structlog.get_logger()


async def run_job(engine: WorkflowEngine, job: jobs.ClaimedJob) -> None:
    run_id = uuid.UUID(job.payload["run_id"])
    if job.kind == STEP_JOB:
        await engine.step(job.tenant_id, run_id)
    elif job.kind == ACTIONS_JOB:
        await engine.apply_actions(job.tenant_id, run_id)
    else:
        raise ValueError(f"unknown job kind {job.kind}")


async def _execute(engine: WorkflowEngine, job: jobs.ClaimedJob) -> None:
    try:
        await run_job(engine, job)
    except Exception as exc:
        logger.exception("job.failed", job_id=str(job.id), kind=job.kind, attempt=job.attempts)
        async with system_session() as session:
            await jobs.mark_failed(session, job, f"{type(exc).__name__}: {exc}")
    else:
        async with system_session() as session:
            await jobs.mark_done(session, job.id)


async def main() -> None:
    settings = get_settings()
    configure_logging(json_output=settings.environment != "development")
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    engine = build_engine(settings)
    stopping = asyncio.Event()
    tasks: set[asyncio.Task[None]] = set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):  # Windows dev machines
            loop.add_signal_handler(sig, stopping.set)

    logger.info("worker.started", worker_id=worker_id, telephony=settings.telephony_backend)
    while not stopping.is_set():
        free = settings.worker_concurrency - len(tasks)
        claimed: list[jobs.ClaimedJob] = []
        if free > 0:
            try:
                async with system_session() as session:
                    claimed = await jobs.claim_due(session, worker_id, free)
            except Exception:
                logger.exception("worker.claim_failed")
        for job in claimed:
            task = asyncio.create_task(_execute(engine, job))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        if not claimed or free <= 0:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stopping.wait(), timeout=settings.worker_poll_seconds)

    logger.info("worker.stopping", in_flight=len(tasks))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    await dispose_engines()


if __name__ == "__main__":
    asyncio.run(main())
