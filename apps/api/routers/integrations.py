"""Integration settings and the do-not-call list."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

import phonenumbers
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.api.dependencies import Context, SettingsDep, require
from modules.compliance.application import dnc
from modules.integrations.application import store
from modules.integrations.application.store import IntegrationError

router = APIRouter(prefix="/v1", tags=["integrations"])

ManageIntegrations = Annotated[Context, Depends(require("integrations.manage"))]
ManageDnc = Annotated[Context, Depends(require("dnc.manage"))]


@router.get("/integrations")
async def list_integrations(ctx: ManageIntegrations, settings: SettingsDep) -> list[dict[str, Any]]:
    return await store.public_view(ctx.session, ctx.tenant_id, settings.public_base_url.rstrip("/"))


@router.put("/integrations/{provider}")
async def save_integration(provider: str, body: dict[str, Any], ctx: ManageIntegrations) -> dict[str, Any]:
    await store.save(ctx.session, ctx.tenant_id, ctx.user_id, provider, body)
    return {"ok": True}


@router.delete("/integrations/{provider}", status_code=204)
async def remove_integration(provider: str, ctx: ManageIntegrations) -> None:
    await store.remove(ctx.session, ctx.tenant_id, ctx.user_id, provider)


class DncIn(BaseModel):
    phone: str = Field(min_length=6, max_length=32)


def _e164(raw: str, country: str) -> str:
    try:
        number = phonenumbers.parse(raw, country)
    except phonenumbers.NumberParseException as exc:
        raise IntegrationError(422, "Enter a valid phone number") from exc
    if not phonenumbers.is_valid_number(number):
        raise IntegrationError(422, "Enter a valid phone number")
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


@router.get("/dnc")
async def list_dnc(ctx: ManageDnc) -> list[dict[str, Any]]:
    return [
        {"id": str(e.id), "phone_last4": e.phone_last4, "reason": e.reason, "created_at": e.created_at}
        for e in await dnc.list_entries(ctx.session)
    ]


@router.post("/dnc", status_code=201)
async def add_dnc(body: DncIn, ctx: ManageDnc) -> dict[str, Any]:
    await dnc.add(ctx.session, ctx.tenant_id, _e164(body.phone, ctx.principal.tenant.country), "manual", ctx.user_id)
    return {"ok": True}


@router.delete("/dnc/{entry_id}", status_code=204)
async def remove_dnc(entry_id: uuid.UUID, ctx: ManageDnc) -> None:
    if not await dnc.remove(ctx.session, entry_id):
        raise IntegrationError(404, "Entry not found")
