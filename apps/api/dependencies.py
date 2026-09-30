"""FastAPI dependency injection."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import Depends, HTTPException, Request
from modules.tenancy.adapters.database import get_db_session
from modules.tenancy.domain.settings import Settings, get_settings
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = structlog.get_logger()

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_current_tenant(request: Request) -> uuid.UUID:
    """Extract tenant ID from the authenticated request."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return tenant_id


CurrentTenant = Annotated[uuid.UUID, Depends(get_current_tenant)]


async def get_session(tenant_id: CurrentTenant) -> AsyncIterator[AsyncSession]:
    """Provide a tenant-scoped database session."""
    async for session in get_db_session(tenant_id):
        yield session


DBSession = Annotated[AsyncSession, Depends(get_session)]
