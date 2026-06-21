"""add discount codes

Revision ID: 20260605_0010
Revises: 20260604_0009
Create Date: 2026-06-05
"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260605_0010"
down_revision: str | None = "20260604_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return {table_name.upper() for table_name in inspect(op.get_bind()).get_table_names()}


def _columns(table_name: str) -> set[str]:
    inspector = inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _foreign_keys(table_name: str) -> set[str]:
    inspector = inspect(op.get_bind())
    return {fk["name"] for fk in inspector.get_foreign_keys(table_name) if fk.get("name")}


def upgrade() -> None:
    tables = _tables()
    if "MA_GIAM_GIA" not in tables:
        op.create_table(
            "MA_GIAM_GIA",
            sa.Column("id_ma_giam_gia", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("ma_code", sa.String(length=50), nullable=False, unique=True),
            sa.Column("ten_ma", sa.Unicode(length=255), nullable=True),
            sa.Column("mo_ta", sa.Unicode(length=255), nullable=True),
            sa.Column("loai_giam_gia", sa.Enum("phan_tram", "tien_mat", name="loai_giam_gia_ma"), nullable=False),
            sa.Column("gia_tri_giam", sa.DECIMAL(12, 2), nullable=False),
            sa.Column(
                "dieu_kien_loai",
                sa.Enum("so_ngay_thue", "tong_tien_don", "khong_dieu_kien", name="dieu_kien_ma_giam_gia"),
                nullable=True,
                server_default="khong_dieu_kien",
            ),
            sa.Column("so_ngay_thue_toi_thieu", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("gia_tri_don_toi_thieu", sa.DECIMAL(12, 2), nullable=True, server_default="0"),
            sa.Column("ngay_bat_dau", sa.Date(), nullable=True),
            sa.Column("ngay_ket_thuc", sa.Date(), nullable=True),
            sa.Column("so_luong", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("da_su_dung", sa.Integer(), nullable=True, server_default="0"),
            sa.Column(
                "trang_thai",
                sa.Enum("dang_hoat_dong", "tam_ngung", "het_han", name="trang_thai_ma_giam_gia"),
                nullable=True,
                server_default="dang_hoat_dong",
            ),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                nullable=True,
            ),
        )

        op.bulk_insert(
            sa.table(
                "MA_GIAM_GIA",
                sa.column("ma_code", sa.String()),
                sa.column("ten_ma", sa.Unicode()),
                sa.column("mo_ta", sa.Unicode()),
                sa.column("loai_giam_gia", sa.String()),
                sa.column("gia_tri_giam", sa.DECIMAL()),
                sa.column("dieu_kien_loai", sa.String()),
                sa.column("so_ngay_thue_toi_thieu", sa.Integer()),
                sa.column("gia_tri_don_toi_thieu", sa.DECIMAL()),
                sa.column("ngay_bat_dau", sa.Date()),
                sa.column("ngay_ket_thuc", sa.Date()),
                sa.column("so_luong", sa.Integer()),
                sa.column("da_su_dung", sa.Integer()),
                sa.column("trang_thai", sa.String()),
            ),
            [
                {
                    "ma_code": "THUE3NGAY10",
                    "ten_ma": "Thuê 3 ngày giảm 10%",
                    "mo_ta": "Giảm 10% khi thuê từ 3 ngày trở lên",
                    "loai_giam_gia": "phan_tram",
                    "gia_tri_giam": 10,
                    "dieu_kien_loai": "so_ngay_thue",
                    "so_ngay_thue_toi_thieu": 3,
                    "gia_tri_don_toi_thieu": 0,
                    "ngay_bat_dau": date(2026, 1, 1),
                    "ngay_ket_thuc": date(2030, 12, 31),
                    "so_luong": 0,
                    "da_su_dung": 0,
                    "trang_thai": "dang_hoat_dong",
                },
                {
                    "ma_code": "THUE7NGAY20",
                    "ten_ma": "Thuê 7 ngày giảm 20%",
                    "mo_ta": "Giảm 20% khi thuê từ 7 ngày trở lên",
                    "loai_giam_gia": "phan_tram",
                    "gia_tri_giam": 20,
                    "dieu_kien_loai": "so_ngay_thue",
                    "so_ngay_thue_toi_thieu": 7,
                    "gia_tri_don_toi_thieu": 0,
                    "ngay_bat_dau": date(2026, 1, 1),
                    "ngay_ket_thuc": date(2030, 12, 31),
                    "so_luong": 0,
                    "da_su_dung": 0,
                    "trang_thai": "dang_hoat_dong",
                },
                {
                    "ma_code": "GIAM100K",
                    "ten_ma": "Giảm 100.000đ",
                    "mo_ta": "Giảm 100.000đ cho đơn từ 1.000.000đ",
                    "loai_giam_gia": "tien_mat",
                    "gia_tri_giam": 100000,
                    "dieu_kien_loai": "tong_tien_don",
                    "so_ngay_thue_toi_thieu": 0,
                    "gia_tri_don_toi_thieu": 1000000,
                    "ngay_bat_dau": date(2026, 1, 1),
                    "ngay_ket_thuc": date(2030, 12, 31),
                    "so_luong": 0,
                    "da_su_dung": 0,
                    "trang_thai": "dang_hoat_dong",
                },
            ],
        )

    if "DON_THUE" in _tables():
        columns = _columns("DON_THUE")
        if "id_ma_giam_gia" not in columns:
            op.add_column("DON_THUE", sa.Column("id_ma_giam_gia", sa.Integer(), nullable=True))
        if "so_tien_giam" not in columns:
            op.add_column(
                "DON_THUE",
                sa.Column("so_tien_giam", sa.DECIMAL(12, 2), nullable=True, server_default="0"),
            )
        if "fk_don_thue_ma_giam_gia" not in _foreign_keys("DON_THUE"):
            op.create_foreign_key(
                "fk_don_thue_ma_giam_gia",
                "DON_THUE",
                "MA_GIAM_GIA",
                ["id_ma_giam_gia"],
                ["id_ma_giam_gia"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    if "DON_THUE" in _tables():
        fks = _foreign_keys("DON_THUE")
        if "fk_don_thue_ma_giam_gia" in fks:
            op.drop_constraint("fk_don_thue_ma_giam_gia", "DON_THUE", type_="foreignkey")
        columns = _columns("DON_THUE")
        if "so_tien_giam" in columns:
            op.drop_column("DON_THUE", "so_tien_giam")
        if "id_ma_giam_gia" in columns:
            op.drop_column("DON_THUE", "id_ma_giam_gia")

    if "MA_GIAM_GIA" in _tables():
        op.drop_table("MA_GIAM_GIA")
