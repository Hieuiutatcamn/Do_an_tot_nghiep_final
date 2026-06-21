"""add complaint title and product list

Revision ID: 20260604_0009
Revises: 20260604_0008
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260604_0009"
down_revision: str | None = "20260604_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _columns(table_name: str) -> set[str]:
    inspector = inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _columns("KHIEU_NAI")
    if "tieu_de" not in columns:
        op.add_column("KHIEU_NAI", sa.Column("tieu_de", sa.String(length=255), nullable=True))
    if "san_pham_khieu_nai" not in columns:
        op.add_column("KHIEU_NAI", sa.Column("san_pham_khieu_nai", sa.Text(), nullable=True))
    if "noi_dung" in columns:
        op.alter_column("KHIEU_NAI", "noi_dung", existing_type=sa.Unicode(length=255), type_=sa.Text())


def downgrade() -> None:
    columns = _columns("KHIEU_NAI")
    if "san_pham_khieu_nai" in columns:
        op.drop_column("KHIEU_NAI", "san_pham_khieu_nai")
    if "tieu_de" in columns:
        op.drop_column("KHIEU_NAI", "tieu_de")
    if "noi_dung" in columns:
        op.alter_column("KHIEU_NAI", "noi_dung", existing_type=sa.Text(), type_=sa.Unicode(length=255))
