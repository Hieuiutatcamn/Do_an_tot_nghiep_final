"""add complaint date column

Revision ID: 20260522_0004
Revises: 20260522_0003
Create Date: 2026-05-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260522_0004"
down_revision: str | None = "20260522_0003"
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
    if not _has_column("KHIEU_NAI", "ngay_khieu_nai"):
        op.add_column(
            "KHIEU_NAI",
            sa.Column("ngay_khieu_nai", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("KHIEU_NAI", "ngay_khieu_nai"):
        op.drop_column("KHIEU_NAI", "ngay_khieu_nai")
