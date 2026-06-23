"""drop legacy customer avatar column

Revision ID: 20260623_0025
Revises: 20260623_0024
Create Date: 2026-06-23
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260623_0025"
down_revision: str | None = "20260623_0024"
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
    if not _has_table("KHACH_HANG") or not _has_column("KHACH_HANG", "Anh_CCCD"):
        return

    op.execute("ALTER TABLE KHACH_HANG DROP COLUMN Anh_CCCD")


def downgrade() -> None:
    if op.get_bind().dialect.name != "mysql":
        return
    if not _has_table("KHACH_HANG") or _has_column("KHACH_HANG", "Anh_CCCD"):
        return

    op.execute("ALTER TABLE KHACH_HANG ADD COLUMN Anh_CCCD VARCHAR(255) NULL")
    if _has_table("TAI_KHOAN") and _has_column("TAI_KHOAN", "anh_dai_dien") and _has_column("KHACH_HANG", "Id_tai_khoan"):
        op.execute(
            "UPDATE KHACH_HANG kh "
            "JOIN TAI_KHOAN tk ON kh.Id_tai_khoan = tk.id_tai_khoan "
            "SET kh.Anh_CCCD = tk.anh_dai_dien "
            "WHERE tk.anh_dai_dien IS NOT NULL AND tk.anh_dai_dien <> ''"
        )
