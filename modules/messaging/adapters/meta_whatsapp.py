"""WhatsApp Business Cloud API: send confirmation templates and read button replies."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

import httpx

from modules.workflows.ports.channels import WhatsAppRequest

GRAPH_URL = "https://graph.facebook.com"


def verify_signature(body: bytes, header: str | None, app_secret: str) -> bool:
    """X-Hub-Signature-256 is `sha256=<hex HMAC-SHA256(app_secret, raw body)>`."""
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


@dataclass(frozen=True)
class ButtonReply:
    run_id: str
    digit: str


def parse_button_replies(payload: dict[str, Any]) -> list[ButtonReply]:
    """Extract `<run_id>:<digit>` payloads from template quick-reply or interactive button messages."""
    replies = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            for message in (change.get("value") or {}).get("messages") or []:
                raw = None
                if message.get("type") == "button":
                    raw = (message.get("button") or {}).get("payload")
                elif message.get("type") == "interactive":
                    raw = ((message.get("interactive") or {}).get("button_reply") or {}).get("id")
                if raw and raw.count(":") == 1:
                    run_id, digit = raw.split(":")
                    replies.append(ButtonReply(run_id, digit))
    return replies


class MetaWhatsAppSender:
    def __init__(
        self, phone_number_id: str, access_token: str, api_version: str, client: httpx.AsyncClient | None = None
    ) -> None:
        self._url = f"{GRAPH_URL}/{api_version}/{phone_number_id}/messages"
        self._headers = {"Authorization": f"Bearer {access_token}"}
        self._client = client

    @staticmethod
    def build_body(request: WhatsAppRequest) -> dict[str, Any]:
        components: list[dict[str, Any]] = [
            {"type": "body", "parameters": [{"type": "text", "text": p or "-"} for p in request.parameters]}
        ]
        components += [
            {
                "type": "button",
                "sub_type": "quick_reply",
                "index": str(i),
                "parameters": [{"type": "payload", "payload": payload}],
            }
            for i, payload in enumerate(request.button_payloads)
        ]
        return {
            "messaging_product": "whatsapp",
            "to": request.to.lstrip("+"),
            "type": "template",
            "template": {
                "name": request.template_name,
                "language": {"code": request.language},
                "components": components,
            },
        }

    async def send_template(self, request: WhatsAppRequest) -> str:
        body = self.build_body(request)
        if self._client is not None:
            response = await self._client.post(self._url, json=body, headers=self._headers)
        else:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(self._url, json=body, headers=self._headers)
        if response.status_code >= 400:
            raise RuntimeError(f"WhatsApp API {response.status_code}: {response.text[:300]}")
        messages = response.json().get("messages") or [{}]
        return str(messages[0].get("id", ""))
