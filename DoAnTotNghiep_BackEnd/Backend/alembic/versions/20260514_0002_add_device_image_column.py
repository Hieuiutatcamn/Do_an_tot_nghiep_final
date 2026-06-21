"""add device image column

Revision ID: 20260514_0002
Revises: 20260513_0001
Create Date: 2026-05-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260514_0002"
down_revision: str | None = "20260513_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    table_names = {name.lower(): name for name in inspector.get_table_names()}
    actual_table_name = table_names.get(table_name.lower())
    if actual_table_name is None:
        return False

    return any(
        column["name"].lower() == column_name.lower()
        for column in inspector.get_columns(actual_table_name)
    )


def upgrade() -> None:
    if not _has_column("THIET_BI", "hinh_anh"):
        op.add_column("THIET_BI", sa.Column("hinh_anh", sa.String(length=255), nullable=True))


def downgrade() -> None:
    if _has_column("THIET_BI", "hinh_anh"):
        op.drop_column("THIET_BI", "hinh_anh")
