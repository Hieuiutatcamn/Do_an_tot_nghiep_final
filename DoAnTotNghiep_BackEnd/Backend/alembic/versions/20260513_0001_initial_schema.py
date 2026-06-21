"""initial schema

Revision ID: 20260513_0001
Revises:
Create Date: 2026-05-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

revision: str = "20260513_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    tables = _tables()

    if "TAI_KHOAN" not in tables:
        op.create_table(
            "TAI_KHOAN",
            sa.Column("id_tai_khoan", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("Dang_nhap", sa.String(length=50), nullable=False),
            sa.Column("Mat_khau", sa.String(length=100), nullable=False),
            sa.Column("Vai_tro", sa.String(length=20), nullable=True),
            sa.Column("Trang_thai", sa.String(length=20), nullable=True),
            sa.Column("Key", mysql.BIT(length=1), nullable=True),
            sa.UniqueConstraint("Dang_nhap", name="uq_tai_khoan_dang_nhap"),
        )

    tables = _tables()
    if "DANH_MUC" not in tables:
        op.create_table(
            "DANH_MUC",
            sa.Column("Id_danh_muc", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("ten_danh_muc", sa.Unicode(length=100), nullable=True),
            sa.Column("mo_ta", sa.Unicode(length=255), nullable=True),
        )

    tables = _tables()
    if "NHAN_VIEN" not in tables:
        op.create_table(
            "NHAN_VIEN",
            sa.Column("Id_nhan_vien", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("Id_tai_khoan", sa.Integer(), nullable=True),
            sa.Column("ho_ten", sa.Unicode(length=100), nullable=True),
            sa.Column("sdt", sa.Unicode(length=20), nullable=True),
            sa.ForeignKeyConstraint(["Id_tai_khoan"], ["TAI_KHOAN.id_tai_khoan"]),
            sa.UniqueConstraint("Id_tai_khoan", name="uq_nhan_vien_tai_khoan"),
        )

    tables = _tables()
    if "KHACH_HANG" not in tables:
        op.create_table(
            "KHACH_HANG",
            sa.Column("Id_khach_hang", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("Id_tai_khoan", sa.Integer(), nullable=True),
            sa.Column("ho_ten", sa.Unicode(length=100), nullable=True),
            sa.Column("sdt", sa.String(length=20), nullable=True),
            sa.Column("So_CCCD", sa.String(length=20), nullable=True),
            sa.Column("Anh_CCCD_mat_truoc", sa.String(length=255), nullable=True),
            sa.Column("Anh_CCCD_mat_sau", sa.String(length=255), nullable=True),
            sa.Column("email", sa.String(length=100), nullable=True),
            sa.Column("Anh_CCCD", sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(["Id_tai_khoan"], ["TAI_KHOAN.id_tai_khoan"]),
            sa.UniqueConstraint("Id_tai_khoan", name="uq_khach_hang_tai_khoan"),
        )

    tables = _tables()
    if "THIET_BI" not in tables:
        op.create_table(
            "THIET_BI",
            sa.Column("Id_thiet_bi", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("ten_thiet_bi", sa.Unicode(length=100), nullable=False),
            sa.Column("danh_muc_id", sa.Integer(), nullable=True),
            sa.Column("so_luong", sa.Integer(), server_default="0", nullable=True),
            sa.Column("gia_thue", sa.DECIMAL(12, 2), nullable=True),
            sa.Column("tinh_trang", sa.Unicode(length=50), nullable=True),
            sa.Column("mo_ta", sa.Unicode(length=255), nullable=True),
            sa.Column("hinh_anh", sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(["danh_muc_id"], ["DANH_MUC.Id_danh_muc"]),
        )
    elif "hinh_anh" not in _columns("THIET_BI"):
        op.add_column("THIET_BI", sa.Column("hinh_anh", sa.String(length=255), nullable=True))

    tables = _tables()
    if "DON_THUE" not in tables:
        op.create_table(
            "DON_THUE",
            sa.Column("Id_don_thue", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("Id_khach_hang", sa.Integer(), nullable=True),
            sa.Column("ngay_dat", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.Column(
                "trang_thai",
                mysql.ENUM("Cho xac nhan", "Da xac nhan", "Dang thue", "Da thue", "Da qua han", "Da huy"),
                server_default="Cho xac nhan",
                nullable=True,
            ),
            sa.Column("tong_tien", sa.DECIMAL(12, 2), nullable=True),
            sa.Column("Anh_chuyen_khoan", sa.String(length=255), nullable=True),
            sa.Column("ghi_chu", sa.Unicode(length=255), nullable=True),
            sa.ForeignKeyConstraint(["Id_khach_hang"], ["KHACH_HANG.Id_khach_hang"]),
        )

    tables = _tables()
    if "CHI_TIET_DON_THUE" not in tables:
        op.create_table(
            "CHI_TIET_DON_THUE",
            sa.Column("Id_chi_tiet_don_thue", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_don_thue", sa.Integer(), nullable=True),
            sa.Column("id_thiet_bi", sa.Integer(), nullable=True),
            sa.Column("ngay_nhan", sa.DateTime(), nullable=True),
            sa.Column("ngay_tra", sa.DateTime(), nullable=True),
            sa.Column("so_luong", sa.Integer(), nullable=True),
            sa.Column("gia_thue", sa.DECIMAL(10, 2), nullable=True),
            sa.ForeignKeyConstraint(["id_don_thue"], ["DON_THUE.Id_don_thue"]),
            sa.ForeignKeyConstraint(["id_thiet_bi"], ["THIET_BI.Id_thiet_bi"]),
        )

    tables = _tables()
    if "KHIEU_NAI" not in tables:
        op.create_table(
            "KHIEU_NAI",
            sa.Column("Id_khieu_nai", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_don_thue", sa.Integer(), nullable=True),
            sa.Column("id_khach_hang", sa.Integer(), nullable=True),
            sa.Column("noi_dung", sa.Unicode(length=255), nullable=True),
            sa.Column("trang_thai", sa.Unicode(length=50), nullable=True),
            sa.ForeignKeyConstraint(["id_don_thue"], ["DON_THUE.Id_don_thue"]),
            sa.ForeignKeyConstraint(["id_khach_hang"], ["KHACH_HANG.Id_khach_hang"]),
        )


def downgrade() -> None:
    for table_name in (
        "KHIEU_NAI",
        "CHI_TIET_DON_THUE",
        "DON_THUE",
        "THIET_BI",
        "KHACH_HANG",
        "NHAN_VIEN",
        "DANH_MUC",
        "TAI_KHOAN",
    ):
        if table_name in _tables():
            op.drop_table(table_name)
