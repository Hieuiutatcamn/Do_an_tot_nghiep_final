"""normalize pending rental status

Revision ID: 20260613_0013
Revises: 20260607_0012
Create Date: 2026-06-13
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260613_0013"
down_revision: str | None = "20260607_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RENTAL_STATUSES = (
    "Cho xac nhan",
    "Da xac nhan",
    "Dang thue",
    "Da thue",
    "Da qua han",
    "Da huy",
)


def _has_rental_table() -> bool:
    return "DON_THUE" in {
        table_name.upper() for table_name in inspect(op.get_bind()).get_table_names()
    }


def _nullable_clause() -> str:
    columns = inspect(op.get_bind()).get_columns("DON_THUE")
    status_column = next(
        (column for column in columns if column["name"].lower() == "trang_thai"),
        None,
    )
    return "NULL" if status_column and status_column.get("nullable") else "NOT NULL"


def _enum_sql(statuses: tuple[str, ...]) -> str:
    values = ", ".join(f"'{status}'" for status in statuses)
    return f"ENUM({values})"


def upgrade() -> None:
    if not _has_rental_table() or op.get_bind().dialect.name != "mysql":
        return

    nullable = _nullable_clause()
    statuses_with_legacy = ("Da dat", *RENTAL_STATUSES)
    op.execute(
        f"ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(statuses_with_legacy)} {nullable} DEFAULT 'Cho xac nhan'"
    )
    op.execute("UPDATE DON_THUE SET trang_thai = 'Cho xac nhan' WHERE trang_thai = 'Da dat'")
    op.execute(
        f"ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(RENTAL_STATUSES)} {nullable} DEFAULT 'Cho xac nhan'"
    )


def downgrade() -> None:
    if not _has_rental_table() or op.get_bind().dialect.name != "mysql":
        return

    nullable = _nullable_clause()
    statuses_with_legacy = ("Da dat", *RENTAL_STATUSES)
    op.execute(
        f"ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(statuses_with_legacy)} {nullable} DEFAULT 'Da dat'"
    )
    op.execute("UPDATE DON_THUE SET trang_thai = 'Da dat' WHERE trang_thai = 'Cho xac nhan'")
    legacy_statuses = ("Da dat", *RENTAL_STATUSES[1:])
    op.execute(
        f"ALTER TABLE DON_THUE MODIFY COLUMN trang_thai "
        f"{_enum_sql(legacy_statuses)} {nullable} DEFAULT 'Da dat'"
    )
