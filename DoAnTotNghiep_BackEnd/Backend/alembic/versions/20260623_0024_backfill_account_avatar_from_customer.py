"""backfill account avatar from legacy customer image

Revision ID: 20260623_0024
Revises: 20260621_0023
Create Date: 2026-06-23
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260623_0024"
down_revision: str | None = "20260621_0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table_name: str) -> bool:
    return table_name.upper() in {
        current_table.upper() for current_table in inspect(op.get_bind()).get_table_names()
    }


def _has_column(table_name: str, column_name: str) -> bool:
    return any(
        column["name"].lower() == column_name.lower()
        for column in inspect(op.get_bind()).get_columns(table_name)
    )


def upgrade() -> None:
    if op.get_bind().dialect.name != "mysql":
        return
    if not _has_table("TAI_KHOAN") or not _has_table("KHACH_HANG"):
        return
    if not _has_column("TAI_KHOAN", "anh_dai_dien"):
        return
    if not _has_column("KHACH_HANG", "Id_tai_khoan") or not _has_column("KHACH_HANG", "Anh_CCCD"):
        return

    op.execute(
        "UPDATE TAI_KHOAN tk "
        "JOIN KHACH_HANG kh ON kh.Id_tai_khoan = tk.id_tai_khoan "
        "SET tk.anh_dai_dien = kh.Anh_CCCD "
        "WHERE (tk.anh_dai_dien IS NULL OR tk.anh_dai_dien = '') "
        "AND kh.Anh_CCCD IS NOT NULL AND kh.Anh_CCCD <> ''"
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "mysql":
        return
    if not _has_table("TAI_KHOAN") or not _has_table("KHACH_HANG"):
        return
    if not _has_column("TAI_KHOAN", "anh_dai_dien"):
        return
    if not _has_column("KHACH_HANG", "Id_tai_khoan") or not _has_column("KHACH_HANG", "Anh_CCCD"):
        return

    op.execute(
        "UPDATE TAI_KHOAN tk "
        "JOIN KHACH_HANG kh ON kh.Id_tai_khoan = tk.id_tai_khoan "
        "SET tk.anh_dai_dien = NULL "
        "WHERE tk.anh_dai_dien = kh.Anh_CCCD "
        "AND kh.Anh_CCCD IS NOT NULL AND kh.Anh_CCCD <> ''"
    )
