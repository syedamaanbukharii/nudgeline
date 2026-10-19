"""Per-tenant data keys and keyed lookup hashes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from modules.tenancy.adapters.kms_local import LocalKMSAdapter, load_master_key
from modules.tenancy.domain import crypto
from modules.tenancy.domain.models import Tenant

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

_cache: dict[str, bytes] = {}


async def tenant_data_key(session: AsyncSession, tenant_id: uuid.UUID) -> bytes:
    """Return the tenant's plaintext data key, decrypting it once per process."""
    key = _cache.get(str(tenant_id))
    if key is None:
        encrypted = (await session.execute(select(Tenant.data_key_enc).where(Tenant.id == tenant_id))).scalar_one()
        key = await LocalKMSAdapter().decrypt_data_key(str(tenant_id), encrypted)
        _cache[str(tenant_id)] = key
    return key


async def new_tenant_data_key(tenant_id: uuid.UUID) -> bytes:
    """Generate a data key for a new tenant; returns the encrypted form to store."""
    plaintext, encrypted = await LocalKMSAdapter().generate_data_key(str(tenant_id))
    _cache[str(tenant_id)] = plaintext
    return encrypted


def phone_hash(phone_e164: str, tenant_id: uuid.UUID) -> bytes:
    return crypto.lookup_hash(phone_e164, str(tenant_id), load_master_key())
