"""Webhooks router."""

from fastapi import APIRouter, Request, Header, HTTPException
import logging

from modules.integrations.application.webhook_service import WebhookReceiverService

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


# Mock dependencies for MVP
class DummyIdempotencyStore:
    async def exists(self, key): return False
    async def set(self, key, val): pass

class DummySecretProvider:
    async def get_webhook_secret(self, tenant_id, provider): return "dummy_secret"

receiver_service = WebhookReceiverService(
    secret_provider=DummySecretProvider(),
    idempotency_store=DummyIdempotencyStore()
)


@router.post("/{provider}/{tenant_id}")
async def receive_webhook(
    provider: str,
    tenant_id: str,
    request: Request,
    x_signature: str | None = Header(None, alias="X-Signature"),
    x_event_id: str | None = Header(None, alias="X-Event-ID")
):
    """Receive and validate an inbound webhook."""
    if not x_signature or not x_event_id:
        raise HTTPException(status_code=400, detail="Missing signature or event ID")
        
    payload = await request.body()
    
    try:
        await receiver_service.handle_webhook(
            provider=provider,
            tenant_id=tenant_id,
            payload=payload,
            signature=x_signature,
            event_id=x_event_id
        )
    except PermissionError:
        raise HTTPException(status_code=401, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
        
    return {"status": "accepted"}
