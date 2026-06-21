"""normalize rental payment lifecycle into trang_thai

Revision ID: 20260619_0020
Revises: 20260619_0019
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260619_0020"
down_revision: str | None = "20260619_0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRANG_THAI_MOI = (
    "Cho thanh toan",
    "Da dat",
    "Da xac nhan",
    "Dang thue",
    "Da thue",
    "Da huy",
    "Da qua han",
)

TRANG_THAI_CU = (
    "Da dat",
    "Da xac nhan",
    "Dang thue",
    "Da thue",
    "Da qua han",
    "Da huy",
)


def _enum_sql(values: tuple[str, ...]) -> str:
    return "ENUM(" + ", ".join(f"'{value}'" for value in values) + ")"


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("DON_THUE", sa.Column("han_thanh_toan_vnpay", sa.DateTime(), nullable=True))
    op.add_column("DON_THUE", sa.Column("ngay_thanh_toan", sa.DateTime(), nullable=True))

    if bind.dialect.name == "mysql":
        op.execute(
            "ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
            f"{_enum_sql(TRANG_THAI_MOI)} NOT NULL DEFAULT 'Da dat'"
        )
        op.execute(
            """
            UPDATE DON_THUE
            SET trang_thai = 'Cho thanh toan',
                han_thanh_toan_vnpay = COALESCE(
                    han_thanh_toan_vnpay,
                    DATE_ADD(ngay_dat, INTERVAL 15 MINUTE)
                )
            WHERE phuong_thuc_thanh_toan = 'VNPAY'
              AND trang_thai = 'Da dat'
              AND COALESCE(so_tien_da_thanh_toan, 0) = 0
              AND ma_giao_dich_vnpay IS NULL
              AND (
                    trang_thai_thanh_toan = 'Cho thanh toan'
                    OR trang_thai_thanh_toan IS NULL
              )
            """
        )
        op.execute(
            """
            UPDATE DON_THUE
            SET trang_thai = 'Da dat'
            WHERE phuong_thuc_thanh_toan = 'Chuyen khoan thu cong'
              AND trang_thai IN ('Cho thanh toan', 'Da dat')
            """
        )
    else:
        op.execute(
            """
            UPDATE DON_THUE
            SET trang_thai = 'Cho thanh toan'
            WHERE phuong_thuc_thanh_toan = 'VNPAY'
              AND trang_thai = 'Da dat'
              AND COALESCE(so_tien_da_thanh_toan, 0) = 0
              AND ma_giao_dich_vnpay IS NULL
            """
        )

    op.drop_column("DON_THUE", "trang_thai_thanh_toan")


def downgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "DON_THUE",
        sa.Column("trang_thai_thanh_toan", sa.Unicode(50), nullable=True),
    )
    op.execute(
        """
        UPDATE DON_THUE
        SET trang_thai_thanh_toan = CASE
            WHEN phuong_thuc_thanh_toan = 'VNPAY'
                 AND ma_giao_dich_vnpay IS NOT NULL
                THEN 'Da thanh toan'
            WHEN phuong_thuc_thanh_toan = 'VNPAY'
                THEN 'Cho thanh toan'
            WHEN phuong_thuc_thanh_toan = 'Chuyen khoan thu cong'
                THEN 'Cho xac nhan'
            ELSE NULL
        END
        """
    )
    op.execute(
        "UPDATE DON_THUE SET trang_thai = 'Da dat' "
        "WHERE trang_thai = 'Cho thanh toan'"
    )
    if bind.dialect.name == "mysql":
        op.execute(
            "ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
            f"{_enum_sql(TRANG_THAI_CU)} NOT NULL DEFAULT 'Da dat'"
        )
    op.drop_column("DON_THUE", "ngay_thanh_toan")
    op.drop_column("DON_THUE", "han_thanh_toan_vnpay")
