"""add data_key_enc to tenants for envelope encryption

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-28

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("data_key_enc", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "data_key_enc")
