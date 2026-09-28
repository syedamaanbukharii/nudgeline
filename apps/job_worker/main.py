"""arq background worker entry point."""

from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings


async def dispatch_calls(ctx: dict) -> None:  # type: ignore[type-arg]
    """Dispatch scheduled calls."""


async def process_post_call(ctx: dict) -> None:  # type: ignore[type-arg]
    """Run post-call processing pipeline."""


async def process_bulk(ctx: dict) -> None:  # type: ignore[type-arg]
    """Handle bulk operations (CSV import, campaign enrollment)."""


class WorkerSettings:
    """arq worker settings."""

    functions = [dispatch_calls, process_post_call, process_bulk]
    cron_jobs = [
        cron(dispatch_calls, second={0, 30}),
    ]
    redis_settings = RedisSettings(host="valkey", port=6379)
    max_jobs = 50
    job_timeout = 600
