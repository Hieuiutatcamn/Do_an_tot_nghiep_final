"""expand device image column

Revision ID: 20260522_0003
Revises: 20260514_0002
Create Date: 2026-05-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260522_0003"
down_revision: str | None = "20260514_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "THIET_BI",
        "hinh_anh",
        existing_type=sa.String(length=255),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "THIET_BI",
        "hinh_anh",
        existing_type=sa.String(length=2000),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
