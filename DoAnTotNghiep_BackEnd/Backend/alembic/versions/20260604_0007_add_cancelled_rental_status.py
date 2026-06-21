"""add cancelled rental status

Revision ID: 20260604_0007
Revises: 20260603_0006
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260604_0007"
down_revision: str | None = "20260603_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tables() -> set[str]:
    return {table_name.upper() for table_name in inspect(op.get_bind()).get_table_names()}


def upgrade() -> None:
    if "DON_THUE" not in _tables():
        return

    op.execute(
        """
        ALTER TABLE DON_THUE
        MODIFY COLUMN trang_thai ENUM(
            'Cho xac nhan',
            'Da xac nhan',
            'Dang thue',
            'Da thue',
            'Da qua han',
            'Da huy'
        ) NULL DEFAULT 'Cho xac nhan'
        """
    )


def downgrade() -> None:
    if "DON_THUE" not in _tables():
        return

    op.execute("UPDATE DON_THUE SET trang_thai = 'Cho xac nhan' WHERE trang_thai = 'Da huy'")
    op.execute(
        """
        ALTER TABLE DON_THUE
        MODIFY COLUMN trang_thai ENUM(
            'Cho xac nhan',
            'Da xac nhan',
            'Dang thue',
            'Da thue',
            'Da qua han'
        ) NULL DEFAULT 'Cho xac nhan'
        """
    )
