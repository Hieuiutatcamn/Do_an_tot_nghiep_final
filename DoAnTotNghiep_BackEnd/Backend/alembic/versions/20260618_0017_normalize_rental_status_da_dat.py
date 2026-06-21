"""normalize pending rental status to Da dat

Revision ID: 20260618_0017
Revises: 20260617_0016
Create Date: 2026-06-18
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260618_0017"
down_revision: str | None = "20260617_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRANG_THAI_DON_THUE = (
    "Da dat",
    "Da xac nhan",
    "Dang thue",
    "Da thue",
    "Da qua han",
    "Da huy",
)


def _co_bang_don_thue() -> bool:
    return "DON_THUE" in {
        ten_bang.upper() for ten_bang in inspect(op.get_bind()).get_table_names()
    }


def _menh_de_nullable() -> str:
    cac_cot = inspect(op.get_bind()).get_columns("DON_THUE")
    cot_trang_thai = next(
        (cot for cot in cac_cot if cot["name"].lower() == "trang_thai"),
        None,
    )
    return "NULL" if cot_trang_thai and cot_trang_thai.get("nullable") else "NOT NULL"


def _enum_sql(cac_trang_thai: tuple[str, ...]) -> str:
    danh_sach = ", ".join(f"'{trang_thai}'" for trang_thai in cac_trang_thai)
    return f"ENUM({danh_sach})"


def upgrade() -> None:
    if not _co_bang_don_thue() or op.get_bind().dialect.name != "mysql":
        return

    nullable = _menh_de_nullable()
    trang_thai_chuyen_tiep = ("Cho xac nhan", *TRANG_THAI_DON_THUE)
    op.execute(
        "ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(trang_thai_chuyen_tiep)} {nullable} DEFAULT 'Da dat'"
    )
    op.execute(
        "UPDATE DON_THUE SET trang_thai = 'Da dat' "
        "WHERE trang_thai = 'Cho xac nhan'"
    )
    op.execute(
        "ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(TRANG_THAI_DON_THUE)} {nullable} DEFAULT 'Da dat'"
    )


def downgrade() -> None:
    if not _co_bang_don_thue() or op.get_bind().dialect.name != "mysql":
        return

    nullable = _menh_de_nullable()
    trang_thai_cu = (
        "Cho xac nhan",
        "Da xac nhan",
        "Dang thue",
        "Da thue",
        "Da qua han",
        "Da huy",
    )
    trang_thai_chuyen_tiep = ("Da dat", *trang_thai_cu)
    op.execute(
        "ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(trang_thai_chuyen_tiep)} {nullable} DEFAULT 'Cho xac nhan'"
    )
    op.execute(
        "UPDATE DON_THUE SET trang_thai = 'Cho xac nhan' "
        "WHERE trang_thai = 'Da dat'"
    )
    op.execute(
        "ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(trang_thai_cu)} {nullable} DEFAULT 'Cho xac nhan'"
    )
