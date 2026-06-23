"""add status column to rental details

Revision ID: 20260621_0023
Revises: 20260621_0022
Create Date: 2026-06-21
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260621_0023"
down_revision: str | None = "20260621_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CAC_GIA_TRI_TRANG_THAI = (
    "Cho thanh toan",
    "Da dat",
    "Da xac nhan",
    "Dang thue",
    "Da thue",
    "Da huy",
    "Da qua han",
)


def _co_bang_chi_tiet_don_thue() -> bool:
    return "CHI_TIET_DON_THUE" in {
        ten_bang.upper() for ten_bang in inspect(op.get_bind()).get_table_names()
    }


def _co_cot_trang_thai() -> bool:
    cac_cot = inspect(op.get_bind()).get_columns("CHI_TIET_DON_THUE")
    return any(cot["name"].lower() == "trang_thai" for cot in cac_cot)


def _enum_sql(cac_trang_thai: tuple[str, ...]) -> str:
    danh_sach = ", ".join(f"'{trang_thai}'" for trang_thai in cac_trang_thai)
    return f"ENUM({danh_sach})"


def upgrade() -> None:
    if op.get_bind().dialect.name != "mysql" or not _co_bang_chi_tiet_don_thue() or _co_cot_trang_thai():
        return

    op.execute(
        "ALTER TABLE CHI_TIET_DON_THUE "
        f"ADD COLUMN trang_thai {_enum_sql(CAC_GIA_TRI_TRANG_THAI)} "
        "NOT NULL DEFAULT 'Da dat'"
    )
    op.execute(
        "UPDATE CHI_TIET_DON_THUE ct "
        "JOIN DON_THUE d ON ct.id_don_thue = d.id_don_thue "
        "SET ct.trang_thai = d.trang_thai"
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "mysql" or not _co_bang_chi_tiet_don_thue() or not _co_cot_trang_thai():
        return

    op.execute("ALTER TABLE CHI_TIET_DON_THUE DROP COLUMN trang_thai")
