"""Inbound webhooks: Shopify orders, generic orders, WhatsApp replies. Each URL carries a per-integration token."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import orjson
import structlog
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from apps.api.dependencies import SystemSession
from apps.wiring import build_engine
from modules.integrations.adapters import shopify, webhook
from modules.integrations.application import store
from modules.integrations.domain.models import Integration
from modules.messaging.adapters.meta_whatsapp import parse_button_replies, verify_signature
from modules.tenancy.adapters.database import tenant_session
from modules.tenancy.domain.models import Tenant
from modules.workflows.application.ingest import IngestResult, OrderEvent, ingest_order

router = APIRouter(prefix="/v1/hooks", tags=["webhooks"])
logger = structlog.get_logger()


async def _resolve(system: SystemSession, provider: str, token: str) -> tuple[Integration, dict[str, str]]:
    integration = await store.resolve_token(system, provider, token)
    if integration is None:
        raise HTTPException(status_code=404, detail="Unknown webhook")
    return integration, await store.secrets_for(system, integration)


async def _ingest(integration: Integration, event: OrderEvent) -> IngestResult:
    async with tenant_session(integration.tenant_id) as session:
        tenant = await session.get(Tenant, integration.tenant_id)
        assert tenant is not None
        result = await ingest_order(session, tenant, event)
        tracked = await session.get(Integration, integration.id)
        if tracked is not None:
            tracked.last_event_at = datetime.now(UTC)
    logger.info("order.ingested", provider=integration.provider, status=result.status, reason=result.reason)
    return result


def _json(body: bytes) -> dict[str, Any]:
    try:
        data = orjson.loads(body)
    except orjson.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body must be JSON") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    return data


@router.post("/shopify/{token}")
async def shopify_order(token: str, request: Request, system: SystemSession) -> dict[str, Any]:
    integration, secrets = await _resolve(system, "shopify", token)
    body = await request.body()
    if not shopify.verify_webhook(body, request.headers.get("x-shopify-hmac-sha256"), secrets["webhook_secret"]):
        raise HTTPException(status_code=401, detail="Invalid signature")
    if request.headers.get("x-shopify-topic", "orders/create") != "orders/create":
        return {"status": "ignored", "reason": "topic"}
    event = shopify.parse_order(_json(body))
    if event is None:
        return {"status": "ignored", "reason": "no_phone"}
    result = await _ingest(integration, event)
    return {"status": result.status, "reason": result.reason}


@router.post("/orders/{token}")
async def generic_order(token: str, request: Request, system: SystemSession) -> dict[str, Any]:
    integration, secrets = await _resolve(system, "webhook", token)
    body = await request.body()
    if not webhook.verify(body, request.headers.get(webhook.SIGNATURE_HEADER), secrets["signing_secret"]):
        raise HTTPException(status_code=401, detail="Invalid signature")
    try:
        order = webhook.OrderIn.model_validate(_json(body))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc.errors()[0]["msg"])) from exc
    result = await _ingest(integration, order.to_event())
    return {"status": result.status, "run_id": str(result.run_id) if result.run_id else None, "reason": result.reason}


@router.get("/whatsapp/{token}", response_class=PlainTextResponse)
async def whatsapp_verify(
    token: str,
    system: SystemSession,
    mode: str = Query(alias="hub.mode", default=""),
    verify_token: str = Query(alias="hub.verify_token", default=""),
    challenge: str = Query(alias="hub.challenge", default=""),
) -> str:
    _, secrets = await _resolve(system, "whatsapp", token)
    if mode != "subscribe" or verify_token != secrets.get("verify_token"):
        raise HTTPException(status_code=403, detail="Verification failed")
    return challenge


@router.post("/whatsapp/{token}")
async def whatsapp_event(token: str, request: Request, system: SystemSession) -> dict[str, Any]:
    integration, secrets = await _resolve(system, "whatsapp", token)
    body = await request.body()
    if not verify_signature(body, request.headers.get("x-hub-signature-256"), secrets["app_secret"]):
        raise HTTPException(status_code=401, detail="Invalid signature")
    engine = build_engine()
    handled = 0
    for reply in parse_button_replies(_json(body)):
        try:
            run_id = uuid.UUID(reply.run_id)
        except ValueError:
            continue
        if await engine.record_reply(integration.tenant_id, run_id, reply.digit, "whatsapp"):
            handled += 1
    return {"handled": handled}
