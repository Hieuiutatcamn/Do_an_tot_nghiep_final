"""backfill confirmed manual payment deposits

Revision ID: 20260619_0021
Revises: 20260619_0020
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260619_0021"
down_revision: str | None = "20260619_0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE DON_THUE
        SET phuong_thuc_thanh_toan = 'Chuyen khoan thu cong',
            so_tien_da_thanh_toan = 200000
        WHERE Anh_chuyen_khoan IS NOT NULL
          AND TRIM(Anh_chuyen_khoan) <> ''
          AND (
                phuong_thuc_thanh_toan IS NULL
                OR phuong_thuc_thanh_toan <> 'VNPAY'
          )
          AND trang_thai IN (
                'Da xac nhan',
                'Dang thue',
                'Da thue',
                'Da qua han'
          )
          AND COALESCE(so_tien_da_thanh_toan, 0) < 200000
        """
    )


def downgrade() -> None:
    # Không thể phân biệt tiền cọc đã có trước migration với dữ liệu được backfill.
    pass
