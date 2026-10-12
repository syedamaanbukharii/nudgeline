"""Save, load and resolve integrations. Secrets never leave this module unmasked except to adapters."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from modules.integrations.domain.models import PROVIDERS, Integration
from modules.tenancy.application.audit import audit
from modules.tenancy.application.keyring import tenant_data_key
from modules.tenancy.domain.crypto import decrypt_json, encrypt_json

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class IntegrationError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(frozen=True)
class Spec:
    config_fields: tuple[str, ...]
    secret_fields: tuple[str, ...]
    required: tuple[str, ...]
    generated: tuple[str, ...] = ()


SPECS: dict[str, Spec] = {
    "shopify": Spec(
        ("shop_domain",), ("access_token", "webhook_secret"), ("shop_domain", "access_token", "webhook_secret")
    ),
    "webhook": Spec(("callback_url",), ("signing_secret",), (), generated=("signing_secret",)),
    "whatsapp": Spec(
        ("phone_number_id",),
        ("access_token", "app_secret", "verify_token"),
        ("phone_number_id", "access_token", "app_secret"),
        generated=("verify_token",),
    ),
    "telephony": Spec(("sip_trunk_id", "caller_number"), (), ()),
}


@dataclass(frozen=True)
class Connection:
    integration: Integration
    secrets: dict[str, str]

    @property
    def config(self) -> dict[str, Any]:
        return self.integration.config


def _validate(provider: str, config: dict[str, Any]) -> None:
    if provider == "shopify":
        domain = str(config.get("shop_domain", "")).strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9\-]*\.myshopify\.com", domain):
            raise IntegrationError(422, "Shop domain must look like your-store.myshopify.com")
        config["shop_domain"] = domain
    callback = str(config.get("callback_url") or "")
    if provider == "webhook" and callback and not callback.startswith("https://"):
        raise IntegrationError(422, "Callback URL must use https://")


def mask(value: str) -> str:
    return "••••" + value[-4:] if len(value) > 8 else "••••"


async def save(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    provider: str,
    values: dict[str, Any],
) -> Integration:
    """Create or update. Secrets left blank keep their current value."""
    if provider not in PROVIDERS:
        raise IntegrationError(404, "Unknown integration")
    spec = SPECS[provider]
    key = await tenant_data_key(session, tenant_id)
    existing = (await session.execute(select(Integration).where(Integration.provider == provider))).scalar_one_or_none()
    current = decrypt_json(existing.credentials_enc, key) if existing else {}

    config = {f: str(values[f]).strip() for f in spec.config_fields if values.get(f) not in (None, "")}
    creds = {f: str(current[f]) for f in spec.secret_fields if current.get(f)}
    creds.update({f: str(values[f]).strip() for f in spec.secret_fields if values.get(f)})
    for field in spec.generated:
        creds.setdefault(field, secrets.token_urlsafe(32))
    missing = [f for f in spec.required if not (config.get(f) or creds.get(f))]
    if missing:
        raise IntegrationError(422, f"Missing: {', '.join(missing)}")
    _validate(provider, config)

    if existing is None:
        existing = Integration(
            tenant_id=tenant_id,
            provider=provider,
            public_token=secrets.token_urlsafe(24),
            credentials_enc=encrypt_json(creds, key),
            config=config,
        )
        session.add(existing)
    else:
        existing.credentials_enc, existing.config, existing.status = encrypt_json(creds, key), config, "active"
    await session.flush()
    audit(session, tenant_id, user_id, "integration.saved", "integration", provider)
    return existing


async def remove(session: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, provider: str) -> None:
    integration = (
        await session.execute(select(Integration).where(Integration.provider == provider))
    ).scalar_one_or_none()
    if integration is not None:
        await session.delete(integration)
        audit(session, tenant_id, user_id, "integration.removed", "integration", provider)


async def connections(session: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Connection]:
    rows = (await session.execute(select(Integration).where(Integration.status == "active"))).scalars().all()
    if not rows:
        return {}
    key = await tenant_data_key(session, tenant_id)
    return {
        row.provider: Connection(row, {k: str(v) for k, v in decrypt_json(row.credentials_enc, key).items()})
        for row in rows
    }


async def public_view(session: AsyncSession, tenant_id: uuid.UUID, base_url: str) -> list[dict[str, Any]]:
    """What the dashboard shows: config, masked secrets, and the webhook URLs to paste elsewhere."""
    conns = await connections(session, tenant_id)
    result = []
    for provider in PROVIDERS:
        conn = conns.get(provider)
        item: dict[str, Any] = {"provider": provider, "connected": conn is not None}
        if conn is not None:
            token = conn.integration.public_token
            item["config"] = conn.config
            item["secrets"] = {k: mask(v) for k, v in conn.secrets.items()}
            item["last_event_at"] = conn.integration.last_event_at
            item["last_error"] = conn.integration.last_error
            urls = {
                "shopify": f"{base_url}/api/v1/hooks/shopify/{token}",
                "webhook": f"{base_url}/api/v1/hooks/orders/{token}",
                "whatsapp": f"{base_url}/api/v1/hooks/whatsapp/{token}",
            }
            if provider in urls:
                item["webhook_url"] = urls[provider]
            if provider in ("webhook", "whatsapp"):
                shown = "signing_secret" if provider == "webhook" else "verify_token"
                item["reveal"] = {shown: conn.secrets.get(shown)}
        result.append(item)
    return result


async def resolve_token(system: AsyncSession, provider: str, token: str) -> Integration | None:
    """Find the integration a webhook URL belongs to. Use a system session (no tenant known yet)."""
    return (
        await system.execute(
            select(Integration).where(
                Integration.public_token == token, Integration.provider == provider, Integration.status == "active"
            )
        )
    ).scalar_one_or_none()


async def secrets_for(session: AsyncSession, integration: Integration) -> dict[str, str]:
    """Decrypt one integration's secrets (works in a system session after resolve_token)."""
    key = await tenant_data_key(session, integration.tenant_id)
    return {k: str(v) for k, v in decrypt_json(integration.credentials_enc, key).items()}
