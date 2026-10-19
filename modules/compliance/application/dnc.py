"""Do-not-call list operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from modules.compliance.domain.models import DncEntry
from modules.tenancy.application.keyring import phone_hash

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


async def is_blocked(session: AsyncSession, tenant_id: uuid.UUID, phone_e164: str) -> bool:
    digest = phone_hash(phone_e164, tenant_id)
    return (await session.execute(select(DncEntry.id).where(DncEntry.phone_hash == digest))).first() is not None


async def add(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    phone_e164: str,
    reason: str = "manual",
    created_by: uuid.UUID | None = None,
) -> None:
    """Add a number; adding one that is already listed is a no-op."""
    await session.execute(
        insert(DncEntry)
        .values(
            tenant_id=tenant_id,
            phone_hash=phone_hash(phone_e164, tenant_id),
            phone_last4=phone_e164[-4:],
            reason=reason,
            created_by=created_by,
        )
        .on_conflict_do_nothing(constraint="uq_dnc_tenant_phone")
    )


async def list_entries(session: AsyncSession, limit: int = 500) -> list[DncEntry]:
    return list((await session.execute(select(DncEntry).order_by(DncEntry.created_at.desc()).limit(limit))).scalars())


async def remove(session: AsyncSession, entry_id: uuid.UUID) -> bool:
    entry = await session.get(DncEntry, entry_id)
    if entry is None:
        return False
    await session.delete(entry)
    return True
