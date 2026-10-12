"""Shopify: verify order webhooks, map orders, and write outcomes back with the Admin GraphQL API."""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

import httpx

from modules.workflows.application.ingest import OrderEvent
from modules.workflows.ports.channels import OutcomeEvent

_COD_MARKERS = ("cash on delivery", "cod", "الدفع عند الاستلام")


def verify_webhook(body: bytes, header_hmac: str | None, secret: str) -> bool:
    """X-Shopify-Hmac-Sha256 is base64(HMAC-SHA256(secret, raw body))."""
    if not header_hmac:
        return False
    digest = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
    return hmac.compare_digest(digest, header_hmac)


def _is_cod(order: dict[str, Any]) -> bool:
    gateways = [str(g).lower() for g in order.get("payment_gateway_names") or []]
    if any(marker in g for g in gateways for marker in _COD_MARKERS):
        return True
    return order.get("financial_status") == "pending" and not gateways


def parse_order(order: dict[str, Any]) -> OrderEvent | None:
    """Map an orders/create payload. Returns None when there is no phone number to call."""
    customer = order.get("customer") or {}
    shipping = order.get("shipping_address") or {}
    billing = order.get("billing_address") or {}
    phone = order.get("phone") or shipping.get("phone") or customer.get("phone") or billing.get("phone")
    if not phone:
        return None
    name = (
        shipping.get("name")
        or " ".join(p for p in (customer.get("first_name"), customer.get("last_name")) if p)
        or billing.get("name")
        or ""
    )
    return OrderEvent(
        source="shopify",
        external_ref=str(order["id"]),
        customer_name=name.strip(),
        phone=str(phone),
        order_number=str(order.get("name") or order.get("order_number") or ""),
        locale=order.get("customer_locale"),
        total=str(order.get("total_price") or ""),
        currency=order.get("currency"),
        items=[
            {"name": str(li.get("title", ""))[:80], "quantity": int(li.get("quantity") or 1)}
            for li in order.get("line_items") or []
        ],
        is_cod=_is_cod(order),
    )


_TAGS_ADD = """
mutation tagsAdd($id: ID!, $tags: [String!]!) {
  tagsAdd(id: $id, tags: $tags) { userErrors { field message } }
}
"""

_ORDER_CANCEL = """
mutation orderCancel($orderId: ID!) {
  orderCancel(orderId: $orderId, reason: CUSTOMER, refund: false, restock: true, notifyCustomer: false) {
    orderCancelUserErrors { field message }
  }
}
"""


class ShopifyOutcomeSink:
    """Tags the order with the outcome and optionally cancels it."""

    def __init__(self, shop_domain: str, access_token: str, api_version: str, client: httpx.AsyncClient | None = None):
        self._url = f"https://{shop_domain}/admin/api/{api_version}/graphql.json"
        self._headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
        self._client = client

    async def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = {"query": query, "variables": variables}
        if self._client is not None:
            response = await self._client.post(self._url, json=payload, headers=self._headers)
        else:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(self._url, json=payload, headers=self._headers)
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        if body.get("errors"):
            raise RuntimeError(f"Shopify error: {body['errors']}")
        return body.get("data") or {}

    async def apply(self, event: OutcomeEvent) -> None:
        gid = f"gid://shopify/Order/{event.external_ref}"
        if event.tag:
            data = await self._graphql(_TAGS_ADD, {"id": gid, "tags": [event.tag]})
            if errors := (data.get("tagsAdd") or {}).get("userErrors"):
                raise RuntimeError(f"Shopify tagsAdd: {errors}")
        if event.outcome == "cancelled" and event.cancel_order:
            data = await self._graphql(_ORDER_CANCEL, {"orderId": gid})
            if errors := (data.get("orderCancel") or {}).get("orderCancelUserErrors"):
                raise RuntimeError(f"Shopify orderCancel: {errors}")
