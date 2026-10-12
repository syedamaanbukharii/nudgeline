"""Company settings, users and roles."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.dependencies import Context, require
from modules.identity.application import accounts
from modules.identity.domain.models import Role, User
from modules.identity.domain.permissions import PERMISSIONS
from modules.tenancy.application.audit import audit
from modules.tenancy.domain.regions import REGIONS

router = APIRouter(prefix="/v1", tags=["team"])

ManageUsers = Annotated[Context, Depends(require("users.manage"))]
ManageRoles = Annotated[Context, Depends(require("roles.manage"))]
ManageSettings = Annotated[Context, Depends(require("settings.manage"))]


def _user(u: User) -> dict[str, Any]:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "role_id": str(u.role_id),
        "is_active": u.is_active,
        "last_login_at": u.last_login_at,
    }


def _role(r: Role) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "name": r.name,
        "description": r.description,
        "permissions": r.permissions,
        "is_system": r.is_system,
    }


# ── Company settings ───────────────────────────────────────────────


class TenantPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = Field(default=None, max_length=64)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    locale: str | None = Field(default=None, pattern="^(ar|en)$")
    avg_return_cost: float | None = Field(default=None, ge=0, le=100000)


@router.patch("/tenant")
async def update_tenant(body: TenantPatch, ctx: ManageSettings) -> dict[str, Any]:
    tenant = ctx.principal.tenant
    changes = body.model_dump(exclude_none=True)
    if "country" in changes and changes["country"].upper() not in REGIONS:
        raise accounts.AccountError(422, "Unsupported country")
    if "timezone" in changes:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(changes["timezone"])
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise accounts.AccountError(422, "Unknown timezone") from exc
    for field in ("name", "timezone", "locale"):
        if field in changes:
            setattr(tenant, field, changes[field])
    if "country" in changes:
        tenant.country = changes["country"].upper()
    if "currency" in changes:
        tenant.currency = changes["currency"].upper()
    if "avg_return_cost" in changes:
        tenant.settings = {**tenant.settings, "avg_return_cost": changes["avg_return_cost"]}
    audit(ctx.session, tenant.id, ctx.user_id, "tenant.updated", "tenant", tenant.id, changes)
    return {"ok": True}


# ── Users ──────────────────────────────────────────────────────────


class UserIn(BaseModel):
    email: str = Field(max_length=320)
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=10, max_length=200)
    role_id: uuid.UUID


class UserPatch(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role_id: uuid.UUID | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=10, max_length=200)


@router.get("/users")
async def list_users(ctx: ManageUsers) -> list[dict[str, Any]]:
    return [_user(u) for u in await accounts.list_users(ctx.session)]


@router.post("/users", status_code=201)
async def create_user(body: UserIn, ctx: ManageUsers) -> dict[str, Any]:
    user = await accounts.create_user(ctx.session, ctx.principal, **body.model_dump())
    return _user(user)


@router.patch("/users/{user_id}")
async def update_user(user_id: uuid.UUID, body: UserPatch, ctx: ManageUsers) -> dict[str, Any]:
    user = await accounts.update_user(ctx.session, ctx.principal, user_id, **body.model_dump(exclude_none=True))
    return _user(user)


# ── Roles ──────────────────────────────────────────────────────────


class RoleIn(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str = Field(default="", max_length=255)
    permissions: list[str] = Field(default_factory=list)


class RolePatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = Field(default=None, max_length=255)
    permissions: list[str] | None = None


@router.get("/permissions")
async def permissions(ctx: ManageRoles) -> dict[str, str]:
    return PERMISSIONS


@router.get("/roles")
async def list_roles(ctx: Annotated[Context, Depends(require("users.manage"))]) -> list[dict[str, Any]]:
    return [_role(r) for r in await accounts.list_roles(ctx.session)]


@router.post("/roles", status_code=201)
async def create_role(body: RoleIn, ctx: ManageRoles) -> dict[str, Any]:
    return _role(await accounts.create_role(ctx.session, ctx.principal, **body.model_dump()))


@router.patch("/roles/{role_id}")
async def update_role(role_id: uuid.UUID, body: RolePatch, ctx: ManageRoles) -> dict[str, Any]:
    return _role(await accounts.update_role(ctx.session, ctx.principal, role_id, **body.model_dump(exclude_none=True)))


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(role_id: uuid.UUID, ctx: ManageRoles) -> None:
    await accounts.delete_role(ctx.session, ctx.principal, role_id)
