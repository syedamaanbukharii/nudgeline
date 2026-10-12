"""Database sessions with row-level security tenant isolation.

Two engines exist:

* the app engine connects as a non-superuser role, so Postgres RLS policies apply;
  every tenant session sets ``app.tenant_id`` for the current transaction;
* the system engine connects as the schema owner and bypasses RLS. Use it only for
  work that has no tenant yet (sign-up, login, webhook resolution) or spans tenants
  (the job queue).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from modules.tenancy.domain.settings import get_settings

if TYPE_CHECKING:
    import uuid
    from collections.abc import AsyncIterator

_engines: dict[str, AsyncEngine] = {}
_factories: dict[str, async_sessionmaker[AsyncSession]] = {}


def _factory(kind: str) -> async_sessionmaker[AsyncSession]:
    if kind not in _factories:
        settings = get_settings()
        url = settings.database_url if kind == "app" else settings.database_url_system
        engine = create_async_engine(url, pool_size=10, max_overflow=10, pool_pre_ping=True)
        _engines[kind] = engine
        _factories[kind] = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return _factories[kind]


@asynccontextmanager
async def tenant_session(tenant_id: uuid.UUID) -> AsyncIterator[AsyncSession]:
    """Transactional session scoped to one tenant by RLS. Commits on success."""
    async with _factory("app")() as session:
        await session.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)})
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def system_session() -> AsyncIterator[AsyncSession]:
    """Transactional session that bypasses RLS. Commits on success."""
    async with _factory("system")() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engines() -> None:
    """Close all connection pools (on shutdown and between tests)."""
    for engine in _engines.values():
        await engine.dispose()
    _engines.clear()
    _factories.clear()
