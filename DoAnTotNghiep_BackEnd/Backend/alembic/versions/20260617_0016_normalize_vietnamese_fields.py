"""normalize business fields to Vietnamese

Revision ID: 20260617_0016
Revises: 20260616_0015
Create Date: 2026-06-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260617_0016"
down_revision: str | None = "20260616_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _quote_identifier(value: str) -> str:
    return f"`{value.replace('`', '``')}`"


def _table_lookup() -> dict[str, str]:
    return {table_name.lower(): table_name for table_name in inspect(op.get_bind()).get_table_names()}


def _columns(table_name: str) -> set[str]:
    return {column["name"].lower() for column in inspect(op.get_bind()).get_columns(table_name)}


def _change_column(table_name: str, old_name: str, new_name: str, mysql_type: str, sa_type: sa.types.TypeEngine) -> None:
    actual_table = _table_lookup().get(table_name.lower())
    if not actual_table:
        return

    columns = _columns(actual_table)
    if old_name.lower() not in columns or new_name.lower() in columns:
        return

    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        op.execute(
            "ALTER TABLE "
            f"{_quote_identifier(actual_table)} "
            "CHANGE "
            f"{_quote_identifier(old_name)} "
            f"{_quote_identifier(new_name)} "
            f"{mysql_type}"
        )
        return

    op.alter_column(actual_table, old_name, new_column_name=new_name, existing_type=sa_type)


def _drop_index_if_exists(table_name: str, index_name: str) -> None:
    actual_table = _table_lookup().get(table_name.lower())
    if not actual_table:
        return
    indexes = {index["name"] for index in inspect(op.get_bind()).get_indexes(actual_table)}
    if index_name not in indexes:
        return
    op.drop_index(index_name, table_name=actual_table)


def _create_unique_index_if_missing(table_name: str, index_name: str, columns: list[str]) -> None:
    actual_table = _table_lookup().get(table_name.lower())
    if not actual_table:
        return
    table_columns = _columns(actual_table)
    if not all(column.lower() in table_columns for column in columns):
        return
    indexes = {index["name"] for index in inspect(op.get_bind()).get_indexes(actual_table)}
    if index_name in indexes:
        return
    op.create_index(index_name, actual_table, columns, unique=True)


def _rename_account_unique_index() -> None:
    _drop_index_if_exists("tai_khoan", "uq_tai_khoan_nha_cung_cap_identity")
    _create_unique_index_if_missing(
        "tai_khoan",
        "uq_tai_khoan_nha_cung_cap_dinh_danh",
        ["nha_cung_cap", "id_nha_cung_cap"],
    )


def upgrade() -> None:
    _change_column("tai_khoan", "Key", "kich_hoat", "BIT(1) NULL", sa.Boolean())
    _change_column("tai_khoan", "nha_cung_cap", "nha_cung_cap", "VARCHAR(20) NULL DEFAULT 'local'", sa.String(20))
    _change_column("tai_khoan", "nha_cung_cap_id", "id_nha_cung_cap", "VARCHAR(255) NULL", sa.String(255))
    _change_column("tai_khoan", "anh_dai_dien", "anh_dai_dien", "VARCHAR(500) NULL", sa.String(500))
    _rename_account_unique_index()

    _change_column("khach_hang", "email", "thu_dien_tu", "VARCHAR(100) NULL", sa.String(100))
    _change_column("thiet_bi", "danh_muc_id", "id_danh_muc", "INT NULL", sa.Integer())

    _change_column("ma_giam_gia", "ma_code", "ma_giam_gia", "VARCHAR(50) NOT NULL", sa.String(50))
    _change_column("ma_giam_gia", "created_at", "ngay_tao", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column(
        "ma_giam_gia",
        "updated_at",
        "ngay_cap_nhat",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        sa.DateTime(),
    )

    _change_column("cuoc_tro_chuyen", "chat_mode", "che_do_chat", "ENUM('STAFF') NOT NULL DEFAULT 'STAFF'", sa.String())
    _change_column("cuoc_tro_chuyen", "need_staff", "can_nhan_vien", "TINYINT(1) NULL DEFAULT 0", sa.Boolean())
    _change_column("cuoc_tro_chuyen", "created_at", "ngay_tao", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column(
        "cuoc_tro_chuyen",
        "updated_at",
        "ngay_cap_nhat",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        sa.DateTime(),
    )

    _change_column("tin_nhan_chat", "sender_type", "loai_nguoi_gui", "ENUM('CUSTOMER','STAFF') NOT NULL", sa.String())
    _change_column("tin_nhan_chat", "sender_id", "id_nguoi_gui", "INT NULL", sa.Integer())
    _change_column("tin_nhan_chat", "created_at", "ngay_tao", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())

    _change_column("nhan_vien_online", "id", "id_nhan_vien_online", "INT NOT NULL AUTO_INCREMENT", sa.Integer())
    _change_column("nhan_vien_online", "is_online", "dang_truc_tuyen", "TINYINT(1) NULL DEFAULT 0", sa.Boolean())
    _change_column(
        "nhan_vien_online",
        "last_seen",
        "lan_cuoi_hoat_dong",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        sa.DateTime(),
    )

    _change_column("chat_ticket", "id_ticket", "id_yeu_cau_chat", "INT NOT NULL AUTO_INCREMENT", sa.Integer())
    _change_column(
        "chat_ticket",
        "loai_ticket",
        "loai_yeu_cau",
        "ENUM('KHIEU_NAI','HUY_DON','HOAN_TIEN','CAN_XAC_NHAN','KHAC') NULL DEFAULT 'KHAC'",
        sa.String(),
    )
    _change_column("chat_ticket", "created_at", "ngay_tao", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())

    _change_column(
        "backup_file_chat_before_drop_20260616_231740",
        "file_url",
        "duong_dan_tap_tin",
        "VARCHAR(500) NOT NULL",
        sa.String(500),
    )
    _change_column(
        "backup_file_chat_before_drop_20260616_231740",
        "file_type",
        "loai_tap_tin",
        "VARCHAR(100) NULL",
        sa.String(100),
    )
    _change_column(
        "backup_file_chat_before_drop_20260616_231740",
        "created_at",
        "ngay_tao",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP",
        sa.DateTime(),
    )


def downgrade() -> None:
    _change_column("backup_file_chat_before_drop_20260616_231740", "ngay_tao", "created_at", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column("backup_file_chat_before_drop_20260616_231740", "loai_tap_tin", "file_type", "VARCHAR(100) NULL", sa.String(100))
    _change_column("backup_file_chat_before_drop_20260616_231740", "duong_dan_tap_tin", "file_url", "VARCHAR(500) NOT NULL", sa.String(500))

    _change_column("chat_ticket", "ngay_tao", "created_at", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column(
        "chat_ticket",
        "loai_yeu_cau",
        "loai_ticket",
        "ENUM('KHIEU_NAI','HUY_DON','HOAN_TIEN','CAN_XAC_NHAN','KHAC') NULL DEFAULT 'KHAC'",
        sa.String(),
    )
    _change_column("chat_ticket", "id_yeu_cau_chat", "id_ticket", "INT NOT NULL AUTO_INCREMENT", sa.Integer())

    _change_column(
        "nhan_vien_online",
        "lan_cuoi_hoat_dong",
        "last_seen",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        sa.DateTime(),
    )
    _change_column("nhan_vien_online", "dang_truc_tuyen", "is_online", "TINYINT(1) NULL DEFAULT 0", sa.Boolean())
    _change_column("nhan_vien_online", "id_nhan_vien_online", "id", "INT NOT NULL AUTO_INCREMENT", sa.Integer())

    _change_column("tin_nhan_chat", "ngay_tao", "created_at", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column("tin_nhan_chat", "id_nguoi_gui", "sender_id", "INT NULL", sa.Integer())
    _change_column("tin_nhan_chat", "loai_nguoi_gui", "sender_type", "ENUM('CUSTOMER','STAFF') NOT NULL", sa.String())

    _change_column(
        "cuoc_tro_chuyen",
        "ngay_cap_nhat",
        "updated_at",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        sa.DateTime(),
    )
    _change_column("cuoc_tro_chuyen", "ngay_tao", "created_at", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column("cuoc_tro_chuyen", "can_nhan_vien", "need_staff", "TINYINT(1) NULL DEFAULT 0", sa.Boolean())
    _change_column("cuoc_tro_chuyen", "che_do_chat", "chat_mode", "ENUM('STAFF') NOT NULL DEFAULT 'STAFF'", sa.String())

    _change_column(
        "ma_giam_gia",
        "ngay_cap_nhat",
        "updated_at",
        "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        sa.DateTime(),
    )
    _change_column("ma_giam_gia", "ngay_tao", "created_at", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP", sa.DateTime())
    _change_column("ma_giam_gia", "ma_giam_gia", "ma_code", "VARCHAR(50) NOT NULL", sa.String(50))

    _change_column("thiet_bi", "id_danh_muc", "danh_muc_id", "INT NULL", sa.Integer())
    _change_column("khach_hang", "thu_dien_tu", "email", "VARCHAR(100) NULL", sa.String(100))

    _drop_index_if_exists("tai_khoan", "uq_tai_khoan_nha_cung_cap_dinh_danh")
    _change_column("tai_khoan", "anh_dai_dien", "anh_dai_dien", "VARCHAR(500) NULL", sa.String(500))
    _change_column("tai_khoan", "id_nha_cung_cap", "nha_cung_cap_id", "VARCHAR(255) NULL", sa.String(255))
    _change_column("tai_khoan", "nha_cung_cap", "nha_cung_cap", "VARCHAR(20) NULL DEFAULT 'local'", sa.String(20))
    _change_column("tai_khoan", "kich_hoat", "Key", "BIT(1) NULL", sa.Boolean())
    _create_unique_index_if_missing(
        "tai_khoan",
        "uq_tai_khoan_nha_cung_cap_identity",
        ["nha_cung_cap", "nha_cung_cap_id"],
    )
