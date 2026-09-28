"""Compliance engine domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.tenancy.domain.models import Base


class RulePack(Base):
    """Compliance rules per jurisdiction."""

    __tablename__ = "rule_packs"
    __table_args__ = (
        sa.UniqueConstraint("jurisdiction", "version", name="uq_rule_packs_jurisdiction_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    jurisdiction: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    effective_from: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    approved_by: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    

class ComplianceDecision:
    """A business logic result for whether a dial is allowed."""
    
    def __init__(self, allowed: bool, reason: str):
        self.allowed = allowed
        self.reason = reason
