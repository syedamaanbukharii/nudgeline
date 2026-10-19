"""Audit trail helper."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modules.tenancy.domain.models import AuditLogEntry

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


def audit(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: object,
    changes: dict[str, Any] | None = None,
) -> None:
    """Record who changed what, in the caller's transaction."""
    session.add(
        AuditLogEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            changes=changes,
        )
    )
