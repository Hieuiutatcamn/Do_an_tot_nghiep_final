"""remove automated chat data and keep customer-staff conversations

Revision ID: 20260618_0018
Revises: 20260618_0017
Create Date: 2026-06-18
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260618_0018"
down_revision: str | None = "20260618_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _quote_identifier(value: str) -> str:
    return f"`{value.replace('`', '``')}`"


def _table_lookup() -> dict[str, str]:
    return {table_name.lower(): table_name for table_name in inspect(op.get_bind()).get_table_names()}


def _column_lookup(table_name: str) -> dict[str, str]:
    return {
        column["name"].lower(): column["name"]
        for column in inspect(op.get_bind()).get_columns(table_name)
    }


def _drop_table_if_exists(table_name: str) -> None:
    actual_name = _table_lookup().get(table_name.lower())
    if actual_name:
        op.drop_table(actual_name)


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "mysql":
        op.execute("DROP PROCEDURE IF EXISTS sp_gui_tin_nhan")
        op.execute("DROP PROCEDURE IF EXISTS sp_lich_su_chat")

    for table_name in (
        "file_chat",
        "backup_file_chat_before_drop_20260616_231740",
        "tin_nhan",
        "tin_nhan_ai",
        "lich_su_chat_ai",
        "phan_hoi_ai",
        "webhook_ai",
    ):
        _drop_table_if_exists(table_name)

    conversation_table = _table_lookup().get("cuoc_tro_chuyen")
    if conversation_table:
        columns = _column_lookup(conversation_table)
        mode_column = columns.get("che_do_chat") or columns.get("chat_mode")
        status_column = columns.get("trang_thai")
        need_staff_column = columns.get("can_nhan_vien") or columns.get("need_staff")

        if mode_column:
            op.execute(
                f"UPDATE {_quote_identifier(conversation_table)} "
                f"SET {_quote_identifier(mode_column)} = 'STAFF' "
                f"WHERE {_quote_identifier(mode_column)} <> 'STAFF'"
            )
        if status_column:
            op.execute(
                f"UPDATE {_quote_identifier(conversation_table)} "
                f"SET {_quote_identifier(status_column)} = 'CHO_NHAN_VIEN' "
                f"WHERE {_quote_identifier(status_column)} = 'AI_DANG_XU_LY'"
            )
        if status_column and need_staff_column:
            op.execute(
                f"UPDATE {_quote_identifier(conversation_table)} "
                f"SET {_quote_identifier(need_staff_column)} = 1 "
                f"WHERE {_quote_identifier(status_column)} = 'CHO_NHAN_VIEN'"
            )

        if bind.dialect.name == "mysql":
            if mode_column:
                op.execute(
                    f"ALTER TABLE {_quote_identifier(conversation_table)} "
                    f"MODIFY COLUMN {_quote_identifier(mode_column)} "
                    "ENUM('STAFF') NOT NULL DEFAULT 'STAFF'"
                )
            if status_column:
                op.execute(
                    f"ALTER TABLE {_quote_identifier(conversation_table)} "
                    f"MODIFY COLUMN {_quote_identifier(status_column)} "
                    "ENUM('CHO_NHAN_VIEN','NHAN_VIEN_DANG_XU_LY','DA_DONG') "
                    "NOT NULL DEFAULT 'CHO_NHAN_VIEN'"
                )

    message_table = _table_lookup().get("tin_nhan_chat")
    if message_table:
        columns = _column_lookup(message_table)
        sender_column = columns.get("loai_nguoi_gui") or columns.get("sender_type")
        if sender_column:
            op.execute(
                f"DELETE FROM {_quote_identifier(message_table)} "
                f"WHERE {_quote_identifier(sender_column)} = 'AI'"
            )
            if bind.dialect.name == "mysql":
                op.execute(
                    f"ALTER TABLE {_quote_identifier(message_table)} "
                    f"MODIFY COLUMN {_quote_identifier(sender_column)} "
                    "ENUM('CUSTOMER','STAFF') NOT NULL"
                )


def downgrade() -> None:
    # Dữ liệu trả lời tự động đã xóa không thể khôi phục an toàn.
    pass
