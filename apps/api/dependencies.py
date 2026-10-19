"""Request authentication, tenant-scoped sessions and permission checks."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from modules.identity.application.accounts import Principal, load_principal
from modules.identity.domain.security import read_token
from modules.tenancy.adapters.database import system_session, tenant_session
from modules.tenancy.domain.settings import Settings, get_settings

SESSION_COOKIE = "session"

SettingsDep = Annotated[Settings, Depends(get_settings)]


@dataclass(frozen=True)
class Context:
    session: AsyncSession
    principal: Principal

    @property
    def tenant_id(self):  # noqa: ANN201 - uuid.UUID
        return self.principal.tenant.id

    @property
    def user_id(self):  # noqa: ANN201 - uuid.UUID
        return self.principal.user.id


def _token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.cookies.get(SESSION_COOKIE)


async def _context(request: Request, settings: SettingsDep) -> AsyncIterator[Context]:
    token = _token(request)
    claims = read_token(token, settings.secret_key) if token else None
    if claims is None:
        raise HTTPException(status_code=401, detail="Sign in required")
    async with tenant_session(claims.tenant_id) as session:
        principal = await load_principal(session, claims.user_id)
        if principal is None:
            raise HTTPException(status_code=401, detail="Sign in required")
        yield Context(session, principal)


Ctx = Annotated[Context, Depends(_context, scope="function")]


def require(permission: str) -> Callable[[Context], Context]:
    """Dependency factory: the signed-in user's role must grant `permission`."""

    def check(ctx: Ctx) -> Context:
        if not ctx.principal.can(permission):
            raise HTTPException(status_code=403, detail="Your role doesn't allow this")
        return ctx

    return check


async def _system() -> AsyncIterator[AsyncSession]:
    async with system_session() as session:
        yield session


SystemSession = Annotated[AsyncSession, Depends(_system, scope="function")]
