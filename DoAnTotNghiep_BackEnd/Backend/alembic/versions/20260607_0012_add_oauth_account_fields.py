"""add oauth account fields

Revision ID: 20260607_0012
Revises: 20260607_0011
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260607_0012"
down_revision: str | None = "20260607_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _columns() -> set[str]:
    return {column["name"].lower() for column in inspect(op.get_bind()).get_columns("TAI_KHOAN")}


def _unique_names() -> set[str]:
    return {
        item["name"]
        for item in inspect(op.get_bind()).get_unique_constraints("TAI_KHOAN")
        if item.get("name")
    }


def upgrade() -> None:
    columns = _columns()
    if "nha_cung_cap" not in columns:
        op.add_column("TAI_KHOAN", sa.Column("nha_cung_cap", sa.String(length=20), nullable=True, server_default="local"))
    if "nha_cung_cap_id" not in columns:
        op.add_column("TAI_KHOAN", sa.Column("nha_cung_cap_id", sa.String(length=255), nullable=True))
    if "anh_dai_dien" not in columns:
        op.add_column("TAI_KHOAN", sa.Column("anh_dai_dien", sa.String(length=500), nullable=True))

    op.execute(sa.text("UPDATE TAI_KHOAN SET nha_cung_cap = 'local' WHERE nha_cung_cap IS NULL OR nha_cung_cap = ''"))
    if "uq_tai_khoan_nha_cung_cap_identity" not in _unique_names():
        op.create_unique_constraint(
            "uq_tai_khoan_nha_cung_cap_identity",
            "TAI_KHOAN",
            ["nha_cung_cap", "nha_cung_cap_id"],
        )


def downgrade() -> None:
    if "uq_tai_khoan_nha_cung_cap_identity" in _unique_names():
        op.drop_constraint("uq_tai_khoan_nha_cung_cap_identity", "TAI_KHOAN", type_="unique")
    columns = _columns()
    for column_name in ("anh_dai_dien", "nha_cung_cap_id", "nha_cung_cap"):
        if column_name in columns:
            op.drop_column("TAI_KHOAN", column_name)
