"""add ai chat history (tin_nhan_ai)

Revision ID: 20260621_0022
Revises: 20260619_0021
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

revision: str = "20260621_0022"
down_revision: str | None = "20260619_0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    if "tin_nhan_ai" not in _tables():
        op.create_table(
            "tin_nhan_ai",
            sa.Column("id_tin_nhan_ai", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_khach_hang", sa.Integer(), nullable=False),
            sa.Column("vai_tro", mysql.ENUM("USER", "AI"), nullable=False),
            sa.Column("noi_dung", sa.Text(), nullable=False),
            sa.Column("ngay_tao", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.ForeignKeyConstraint(["id_khach_hang"], ["KHACH_HANG.Id_khach_hang"]),
        )
        op.create_index("ix_tin_nhan_ai_khach_hang", "tin_nhan_ai", ["id_khach_hang"])


def downgrade() -> None:
    if "tin_nhan_ai" in _tables():
        op.drop_table("tin_nhan_ai")
