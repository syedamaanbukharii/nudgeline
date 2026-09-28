"""Database session management with RLS tenant isolation."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from modules.tenancy.domain.settings import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    """Get or create the async engine."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.environment == "development",
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory  # noqa: PLW0603
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_db_session(
    tenant_id: uuid.UUID | None = None,
) -> AsyncIterator[AsyncSession]:
    """Provide a transactional database session with RLS.

    Sets ``app.tenant_id`` via ``SET LOCAL`` so that Postgres RLS policies
    scope every query to the current tenant. SET LOCAL is transaction-scoped
    and automatically cleared on COMMIT/ROLLBACK.
    """
    factory = get_session_factory()
    async with factory() as session:
        if tenant_id is not None:
            await session.execute(
                text("SET LOCAL app.tenant_id = :tid"),
                {"tid": str(tenant_id)},
            )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
