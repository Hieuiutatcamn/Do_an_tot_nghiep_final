"""add cart and notifications tables

Revision ID: 20260601_0005
Revises: 20260522_0004
Create Date: 2026-06-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

revision: str = "20260601_0005"
down_revision: str | None = "20260522_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return {table_name.upper() for table_name in inspect(op.get_bind()).get_table_names()}


def upgrade() -> None:
    tables = _tables()

    if "GIO_HANG" not in tables:
        op.create_table(
            "GIO_HANG",
            sa.Column("Id_gio_hang", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("Id_khach_hang", sa.Integer(), nullable=False),
            sa.Column("Id_thiet_bi", sa.Integer(), nullable=False),
            sa.Column("so_luong", sa.Integer(), server_default="1", nullable=True),
            sa.Column("ngay_nhan", sa.Date(), nullable=True),
            sa.Column("ngay_tra", sa.Date(), nullable=True),
            sa.Column("ngay_them", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.ForeignKeyConstraint(["Id_khach_hang"], ["KHACH_HANG.Id_khach_hang"]),
            sa.ForeignKeyConstraint(["Id_thiet_bi"], ["THIET_BI.Id_thiet_bi"]),
        )

    tables = _tables()
    if "THONG_BAO" not in tables:
        op.create_table(
            "THONG_BAO",
            sa.Column("Id_thong_bao", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("Id_tai_khoan", sa.Integer(), nullable=True),
            sa.Column("Id_don_thue", sa.Integer(), nullable=True),
            sa.Column("tieu_de", sa.Unicode(length=100), nullable=True),
            sa.Column("noi_dung", sa.Unicode(length=255), nullable=True),
            sa.Column(
                "loai_thong_bao",
                mysql.ENUM(
                    "Dat hang thanh cong",
                    "Co don hang moi",
                    "Cap nhat don hang",
                    "Khieu nai",
                    "He thong",
                ),
                nullable=True,
            ),
            sa.Column(
                "doi_tuong_nhan",
                mysql.ENUM("User", "Admin", "Nhan vien"),
                nullable=True,
            ),
            sa.Column(
                "trang_thai",
                mysql.ENUM("Chua doc", "Da doc"),
                server_default="Chua doc",
                nullable=True,
            ),
            sa.Column("ngay_tao", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.ForeignKeyConstraint(["Id_tai_khoan"], ["TAI_KHOAN.id_tai_khoan"]),
            sa.ForeignKeyConstraint(["Id_don_thue"], ["DON_THUE.Id_don_thue"]),
        )


def downgrade() -> None:
    tables = _tables()
    if "THONG_BAO" in tables:
        op.drop_table("THONG_BAO")
    tables = _tables()
    if "GIO_HANG" in tables:
        op.drop_table("GIO_HANG")
