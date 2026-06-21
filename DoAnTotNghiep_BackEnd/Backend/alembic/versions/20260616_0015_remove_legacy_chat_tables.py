"""remove legacy chat tables

Revision ID: 20260616_0015
Revises: 20260614_0014
Create Date: 2026-06-16
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260616_0015"
down_revision: str | None = "20260614_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_lookup() -> dict[str, str]:
    return {table_name.lower(): table_name for table_name in inspect(op.get_bind()).get_table_names()}


def _quote_identifier(value: str) -> str:
    return f"`{value.replace('`', '``')}`"


def _drop_foreign_keys(table_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    for foreign_key in inspector.get_foreign_keys(table_name):
        constraint_name = foreign_key.get("name")
        if not constraint_name:
            continue
        if bind.dialect.name == "mysql":
            op.execute(
                "ALTER TABLE "
                f"{_quote_identifier(table_name)} "
                "DROP FOREIGN KEY "
                f"{_quote_identifier(constraint_name)}"
            )
        else:
            op.drop_constraint(constraint_name, table_name, type_="foreignkey")


def _drop_table_if_exists(table_name: str) -> None:
    actual_name = _table_lookup().get(table_name.lower())
    if not actual_name:
        return
    _drop_foreign_keys(actual_name)
    op.drop_table(actual_name)


def _drop_legacy_routines() -> None:
    if op.get_bind().dialect.name != "mysql":
        return
    op.execute("DROP PROCEDURE IF EXISTS sp_gui_tin_nhan")
    op.execute("DROP PROCEDURE IF EXISTS sp_lich_su_chat")


def upgrade() -> None:
    _drop_legacy_routines()
    _drop_table_if_exists("file_chat")
    _drop_table_if_exists("tin_nhan")


def downgrade() -> None:
    # Các bảng cũ đã bị loại bỏ vĩnh viễn và không được tái tạo khi downgrade.
    pass
