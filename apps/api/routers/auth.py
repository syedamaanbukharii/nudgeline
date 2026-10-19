"""Sign-up, login, logout and the current user."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from apps.api.dependencies import SESSION_COOKIE, Ctx, SettingsDep, SystemSession
from modules.identity.application.accounts import authenticate, sign_up
from modules.identity.domain.permissions import PERMISSIONS
from modules.identity.domain.security import TokenClaims, issue_token
from modules.tenancy.domain.regions import REGIONS

router = APIRouter(prefix="/v1", tags=["auth"])


class SignUpIn(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=320)
    password: str = Field(min_length=10, max_length=200)
    country: str = Field(default="AE", min_length=2, max_length=2)


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)


def _set_session(response: Response, settings: SettingsDep, claims: TokenClaims) -> str:
    token = issue_token(claims, settings.secret_key, settings.access_token_ttl_minutes)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.access_token_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return token


@router.post("/auth/signup", status_code=201)
async def signup(body: SignUpIn, response: Response, settings: SettingsDep, system: SystemSession) -> dict[str, Any]:
    user = await sign_up(
        system,
        company_name=body.company_name,
        full_name=body.full_name,
        email=body.email,
        password=body.password,
        country=body.country,
    )
    token = _set_session(response, settings, TokenClaims(user.id, user.tenant_id))
    return {"user_id": str(user.id), "tenant_id": str(user.tenant_id), "token": token}


@router.post("/auth/login")
async def login(body: LoginIn, response: Response, settings: SettingsDep, system: SystemSession) -> dict[str, Any]:
    user = await authenticate(system, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    token = _set_session(response, settings, TokenClaims(user.id, user.tenant_id))
    return {"user_id": str(user.id), "tenant_id": str(user.tenant_id), "token": token}


@router.post("/auth/logout", status_code=204)
async def logout(response: Response, settings: SettingsDep) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", secure=settings.cookie_secure, httponly=True, samesite="lax")


@router.get("/me")
async def me(ctx: Ctx, settings: SettingsDep) -> dict[str, Any]:
    p = ctx.principal
    return {
        "user": {"id": str(p.user.id), "email": p.user.email, "full_name": p.user.full_name},
        "role": {"id": str(p.role.id), "name": p.role.name, "is_system": p.role.is_system},
        "permissions": sorted(p.permissions),
        "tenant": {
            "id": str(p.tenant.id),
            "name": p.tenant.name,
            "country": p.tenant.country,
            "timezone": p.tenant.timezone,
            "currency": p.tenant.currency,
            "locale": p.tenant.locale,
            "avg_return_cost": p.tenant.settings.get("avg_return_cost", 0),
        },
        "brand_name": settings.brand_name,
    }


@router.get("/meta")
async def meta(settings: SettingsDep) -> dict[str, Any]:
    """Public, unauthenticated: what the sign-up form needs."""
    return {
        "brand_name": settings.brand_name,
        "countries": [{"code": c, "currency": r.currency, "timezone": r.timezone} for c, r in REGIONS.items()],
        "permissions": PERMISSIONS,
    }
