"""add VNPAY payment fields to rentals

Revision ID: 20260619_0019
Revises: 20260618_0018
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260619_0019"
down_revision: str | None = "20260618_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "DON_THUE",
        sa.Column("phuong_thuc_thanh_toan", sa.Unicode(50), nullable=True),
    )
    op.add_column(
        "DON_THUE",
        sa.Column("trang_thai_thanh_toan", sa.Unicode(50), nullable=True),
    )
    op.add_column(
        "DON_THUE",
        sa.Column("ma_giao_dich_vnpay", sa.String(100), nullable=True),
    )
    op.add_column(
        "DON_THUE",
        sa.Column(
            "so_tien_da_thanh_toan",
            sa.DECIMAL(12, 2),
            server_default="0",
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("DON_THUE", "so_tien_da_thanh_toan")
    op.drop_column("DON_THUE", "ma_giao_dich_vnpay")
    op.drop_column("DON_THUE", "trang_thai_thanh_toan")
    op.drop_column("DON_THUE", "phuong_thuc_thanh_toan")
