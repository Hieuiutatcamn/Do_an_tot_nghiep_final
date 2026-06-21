"""add customer profile fields

Revision ID: 20260603_0006
Revises: 20260601_0005
Create Date: 2026-06-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260603_0006"
down_revision: str | None = "20260601_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return {table_name.upper() for table_name in inspect(op.get_bind()).get_table_names()}


def _columns(table_name: str) -> set[str]:
    return {column["name"].lower() for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    if "KHACH_HANG" not in _tables():
        return

    columns = _columns("KHACH_HANG")
    if "gioi_tinh" not in columns:
        op.add_column("KHACH_HANG", sa.Column("gioi_tinh", sa.Unicode(length=20), nullable=True))
    if "ngay_sinh" not in columns:
        op.add_column("KHACH_HANG", sa.Column("ngay_sinh", sa.Date(), nullable=True))
    if "dia_chi" not in columns:
        op.add_column("KHACH_HANG", sa.Column("dia_chi", sa.Unicode(length=255), nullable=True))


def downgrade() -> None:
    if "KHACH_HANG" not in _tables():
        return

    columns = _columns("KHACH_HANG")
    if "dia_chi" in columns:
        op.drop_column("KHACH_HANG", "dia_chi")
    if "ngay_sinh" in columns:
        op.drop_column("KHACH_HANG", "ngay_sinh")
    if "gioi_tinh" in columns:
        op.drop_column("KHACH_HANG", "gioi_tinh")
