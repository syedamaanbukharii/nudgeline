"""Generic order webhook for any store or system, plus a signed outcome callback."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

import httpx
import orjson
from pydantic import BaseModel, Field

from modules.workflows.application.ingest import OrderEvent
from modules.workflows.ports.channels import OutcomeEvent

SIGNATURE_HEADER = "X-Signature"
MAX_SKEW_SECONDS = 300


def sign(body: bytes, secret: str, timestamp: int) -> str:
    """`t=<unix>,v1=<hex HMAC-SHA256(secret, "<t>." + body)>`"""
    mac = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={mac}"


def verify(body: bytes, header: str | None, secret: str, now: int | None = None) -> bool:
    if not header:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    try:
        timestamp = int(parts["t"])
    except (KeyError, ValueError):
        return False
    if abs((now or int(time.time())) - timestamp) > MAX_SKEW_SECONDS:
        return False
    return hmac.compare_digest(sign(body, secret, timestamp), header.replace(" ", ""))


_PREPAID = {"prepaid", "paid", "card", "online", "credit_card", "apple_pay", "wallet"}


def _payment_type(method: str | None) -> str:
    value = (method or "").strip().lower()
    if value in {"cod", "cash", "cash_on_delivery"}:
        return "cod"
    return "prepaid" if value in _PREPAID else "unknown"


class OrderItem(BaseModel):
    name: str = Field(max_length=120)
    quantity: int = Field(default=1, ge=1, le=1000)


class OrderIn(BaseModel):
    """Body of POST /v1/hooks/orders/{token}."""

    external_id: str = Field(min_length=1, max_length=120)
    customer_name: str = Field(default="", max_length=120)
    phone: str = Field(min_length=6, max_length=32)
    order_number: str = Field(default="", max_length=60)
    locale: str | None = Field(default=None, max_length=10)
    total: str | None = Field(default=None, max_length=20)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    items: list[OrderItem] = Field(default_factory=list, max_length=50)
    payment_method: str | None = Field(
        default=None, max_length=40, description="'cod' for cash on delivery; 'prepaid', 'card', 'online' for paid"
    )
    is_first_order: bool | None = None

    def to_event(self) -> OrderEvent:
        return OrderEvent(
            source="webhook",
            external_ref=self.external_id,
            customer_name=self.customer_name,
            phone=self.phone,
            order_number=self.order_number or self.external_id,
            locale=self.locale,
            total=self.total,
            currency=self.currency.upper() if self.currency else None,
            items=[i.model_dump() for i in self.items],
            payment_type=_payment_type(self.payment_method),
            is_first_order=self.is_first_order,
        )


class CallbackOutcomeSink:
    """POSTs the outcome to the customer's callback URL, signed like inbound webhooks."""

    def __init__(self, callback_url: str | None, secret: str, client: httpx.AsyncClient | None = None) -> None:
        self._url = callback_url
        self._secret = secret
        self._client = client

    async def apply(self, event: OutcomeEvent) -> None:
        if not self._url:
            return
        body: dict[str, Any] = {
            "external_id": event.external_ref,
            "order_number": event.order_number,
            "outcome": event.outcome,
            "channel": event.channel,
            "tag": event.tag,
            "cancel_order": event.cancel_order,
            "run_id": str(event.run_id),
        }
        raw = orjson.dumps(body)
        headers = {"Content-Type": "application/json", SIGNATURE_HEADER: sign(raw, self._secret, int(time.time()))}
        if self._client is not None:
            response = await self._client.post(self._url, content=raw, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(self._url, content=raw, headers=headers)
        response.raise_for_status()
