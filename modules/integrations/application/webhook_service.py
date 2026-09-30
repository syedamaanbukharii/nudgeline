"""Webhook receiver service."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebhookReceiverService:
    """Handles incoming webhooks with idempotency and signature validation."""

    def __init__(self, secret_provider: Any, idempotency_store: Any):
        self.secret_provider = secret_provider
        self.idempotency_store = idempotency_store

    async def handle_webhook(
        self, provider: str, tenant_id: str, payload: bytes, signature: str, event_id: str
    ) -> None:
        """Process an incoming webhook securely."""

        # 1. Idempotency Check
        # If we already processed this event_id, skip it.
        if await self.idempotency_store.exists(event_id):
            logger.info(f"Webhook {event_id} already processed. Skipping.")
            return

        # 2. Signature Validation
        secret = await self.secret_provider.get_webhook_secret(tenant_id, provider)
        if not secret:
            logger.warning(f"No webhook secret configured for {provider} / {tenant_id}")
            raise ValueError("Webhook secret not found")

        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        # Note: Depending on provider, signature verification logic (headers, hashes) will differ.
        # This is a generic SHA256 HMAC example.
        if not hmac.compare_digest(expected_sig, signature):
            logger.error("Invalid webhook signature")
            raise PermissionError("Invalid webhook signature")

        # 3. Processing (Enqueue for async processing)
        logger.info(f"Verified webhook {event_id}. Enqueueing for processing.")

        # 4. Mark as processed
        await self.idempotency_store.set(event_id, True)
