"""add customer unique constraints

Revision ID: 20260607_0011
Revises: 20260605_0010
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260607_0011"
down_revision: str | None = "20260605_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UNIQUE_CONSTRAINTS = (
    ("TAI_KHOAN", "Dang_nhap", "uq_tai_khoan_dang_nhap"),
    ("KHACH_HANG", "sdt", "uq_khach_hang_sdt"),
    ("KHACH_HANG", "So_CCCD", "uq_khach_hang_so_cccd"),
    ("KHACH_HANG", "email", "uq_khach_hang_email"),
)


def _unique_constraints(table_name: str) -> list[dict]:
    return inspect(op.get_bind()).get_unique_constraints(table_name)


def _unique_constraint_names(table_name: str) -> set[str]:
    return {
        item["name"]
        for item in _unique_constraints(table_name)
        if item.get("name")
    }


def _has_unique_column(table_name: str, column_name: str) -> bool:
    return any(item.get("column_names") == [column_name] for item in _unique_constraints(table_name))


def _clear_customer_duplicates(column_name: str) -> None:
    customer = sa.table(
        "KHACH_HANG",
        sa.column("Id_khach_hang"),
        sa.column(column_name),
    )
    duplicate_values = op.get_bind().execute(
        sa.select(customer.c[column_name])
        .where(customer.c[column_name].is_not(None), customer.c[column_name] != "")
        .group_by(customer.c[column_name])
        .having(sa.func.count() > 1)
    ).scalars()

    for value in duplicate_values:
        ids = op.get_bind().execute(
            sa.select(customer.c.Id_khach_hang)
            .where(customer.c[column_name] == value)
            .order_by(customer.c.Id_khach_hang.asc())
        ).scalars().all()
        if len(ids) > 1:
            op.get_bind().execute(
                customer.update()
                .where(customer.c.Id_khach_hang.in_(ids[1:]))
                .values({column_name: None})
            )


def upgrade() -> None:
    for column_name in ("sdt", "So_CCCD", "email"):
        _clear_customer_duplicates(column_name)

    for table_name, column_name, constraint_name in UNIQUE_CONSTRAINTS:
        if not _has_unique_column(table_name, column_name):
            op.create_unique_constraint(constraint_name, table_name, [column_name])


def downgrade() -> None:
    for table_name, _, constraint_name in reversed(UNIQUE_CONSTRAINTS):
        if constraint_name in _unique_constraint_names(table_name):
            op.drop_constraint(constraint_name, table_name, type_="unique")
