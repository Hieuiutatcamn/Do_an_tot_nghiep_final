"""add chat conversations

Revision ID: 20260604_0008
Revises: 20260604_0007
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import mysql

revision: str = "20260604_0008"
down_revision: str | None = "20260604_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()

    if "cuoc_tro_chuyen" not in tables:
        op.create_table(
            "cuoc_tro_chuyen",
            sa.Column("id_cuoc_tro_chuyen", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_khach_hang", sa.Integer(), nullable=False),
            sa.Column("id_nhan_vien", sa.Integer(), nullable=True),
            sa.Column("chat_mode", mysql.ENUM("STAFF"), server_default="STAFF", nullable=False),
            sa.Column(
                "trang_thai",
                mysql.ENUM("CHO_NHAN_VIEN", "NHAN_VIEN_DANG_XU_LY", "DA_DONG"),
                server_default="CHO_NHAN_VIEN",
                nullable=False,
            ),
            sa.Column("chu_de", sa.String(length=255), nullable=True),
            sa.Column("need_staff", sa.Boolean(), server_default=sa.text("0"), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["id_khach_hang"], ["KHACH_HANG.Id_khach_hang"]),
            sa.ForeignKeyConstraint(["id_nhan_vien"], ["NHAN_VIEN.Id_nhan_vien"]),
        )
        op.create_index("ix_cuoc_tro_chuyen_khach_hang", "cuoc_tro_chuyen", ["id_khach_hang"])
        op.create_index("ix_cuoc_tro_chuyen_nhan_vien", "cuoc_tro_chuyen", ["id_nhan_vien"])
        op.create_index("ix_cuoc_tro_chuyen_trang_thai", "cuoc_tro_chuyen", ["trang_thai"])
        op.create_index("ix_cuoc_tro_chuyen_created_at", "cuoc_tro_chuyen", ["created_at"])

    tables = _tables()
    if "tin_nhan_chat" not in tables:
        op.create_table(
            "tin_nhan_chat",
            sa.Column("id_tin_nhan", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_cuoc_tro_chuyen", sa.Integer(), nullable=False),
            sa.Column("sender_type", mysql.ENUM("CUSTOMER", "STAFF"), nullable=False),
            sa.Column("sender_id", sa.Integer(), nullable=True),
            sa.Column("noi_dung", sa.Text(), nullable=False),
            sa.Column("loai_tin_nhan", mysql.ENUM("TEXT", "IMAGE", "FILE"), server_default="TEXT", nullable=True),
            sa.Column("da_doc", sa.Boolean(), server_default=sa.text("0"), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.ForeignKeyConstraint(["id_cuoc_tro_chuyen"], ["cuoc_tro_chuyen.id_cuoc_tro_chuyen"]),
        )
        op.create_index("ix_tin_nhan_chat_cuoc_tro_chuyen", "tin_nhan_chat", ["id_cuoc_tro_chuyen"])
        op.create_index("ix_tin_nhan_chat_created_at", "tin_nhan_chat", ["created_at"])

    tables = _tables()
    if "nhan_vien_online" not in tables:
        op.create_table(
            "nhan_vien_online",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_nhan_vien", sa.Integer(), nullable=False),
            sa.Column("is_online", sa.Boolean(), server_default=sa.text("0"), nullable=True),
            sa.Column("last_seen", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.ForeignKeyConstraint(["id_nhan_vien"], ["NHAN_VIEN.Id_nhan_vien"]),
        )
        op.create_index("ix_nhan_vien_online_nhan_vien", "nhan_vien_online", ["id_nhan_vien"], unique=True)
        op.create_index("ix_nhan_vien_online_online", "nhan_vien_online", ["is_online", "last_seen"])

    tables = _tables()
    if "chat_ticket" not in tables:
        op.create_table(
            "chat_ticket",
            sa.Column("id_ticket", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("id_cuoc_tro_chuyen", sa.Integer(), nullable=False),
            sa.Column("id_khach_hang", sa.Integer(), nullable=False),
            sa.Column(
                "loai_ticket",
                mysql.ENUM("KHIEU_NAI", "HUY_DON", "HOAN_TIEN", "CAN_XAC_NHAN", "KHAC"),
                server_default="KHAC",
                nullable=True,
            ),
            sa.Column("noi_dung", sa.Text(), nullable=True),
            sa.Column(
                "trang_thai",
                mysql.ENUM("MOI", "DANG_XU_LY", "DA_XU_LY"),
                server_default="MOI",
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
            sa.ForeignKeyConstraint(["id_cuoc_tro_chuyen"], ["cuoc_tro_chuyen.id_cuoc_tro_chuyen"]),
            sa.ForeignKeyConstraint(["id_khach_hang"], ["KHACH_HANG.Id_khach_hang"]),
        )
        op.create_index("ix_chat_ticket_cuoc_tro_chuyen", "chat_ticket", ["id_cuoc_tro_chuyen"])
        op.create_index("ix_chat_ticket_khach_hang", "chat_ticket", ["id_khach_hang"])
        op.create_index("ix_chat_ticket_trang_thai", "chat_ticket", ["trang_thai"])


def downgrade() -> None:
    tables = _tables()
    if "chat_ticket" in tables:
        op.drop_table("chat_ticket")
    tables = _tables()
    if "nhan_vien_online" in tables:
        op.drop_table("nhan_vien_online")
    tables = _tables()
    if "tin_nhan_chat" in tables:
        op.drop_table("tin_nhan_chat")
    tables = _tables()
    if "cuoc_tro_chuyen" in tables:
        op.drop_table("cuoc_tro_chuyen")
