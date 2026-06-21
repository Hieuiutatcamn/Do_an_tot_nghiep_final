"""normalize Vietnamese notifications and table collations

Revision ID: 20260614_0014
Revises: 20260613_0013
Create Date: 2026-06-14
"""

import re
from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect, text

revision: str = "20260614_0014"
down_revision: str | None = "20260613_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("THONG_BAO", "DON_THUE", "TAI_KHOAN")
TITLE_REPLACEMENTS = {
    "Dat hang thanh cong": "Đặt hàng thành công",
    "Co don hang moi": "Có đơn hàng mới",
    "Huy don hang thanh cong": "Hủy đơn hàng thành công",
    "Khach hang huy don hang": "Khách hàng hủy đơn hàng",
}
CONTENT_PATTERNS = (
    (
        re.compile(r"^Don thue #(\d+) da duoc tao thanh cong\.$"),
        "Đơn thuê #{0} đã được tạo thành công.",
    ),
    (
        re.compile(r"^Don thue #(\d+) vua duoc tao\.$"),
        "Đơn thuê #{0} vừa được tạo.",
    ),
    (
        re.compile(r"^Ban da huy don hang #(?:DH0*)?(\d+) thanh cong\.$"),
        "Bạn đã hủy đơn hàng #{0} thành công.",
    ),
    (
        re.compile(r"^Khach hang da huy don hang #(?:DH0*)?(\d+)\.$"),
        "Khách hàng đã hủy đơn hàng #{0}.",
    ),
)


def _existing_tables() -> set[str]:
    return {
        table_name.upper() for table_name in inspect(op.get_bind()).get_table_names()
    }


def _normalize_content(value: str | None) -> str | None:
    if not value:
        return value
    for pattern, replacement in CONTENT_PATTERNS:
        match = pattern.fullmatch(value)
        if match:
            return replacement.format(match.group(1))
    return value


def _normalize_existing_notifications() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        text("SELECT Id_thong_bao, tieu_de, noi_dung FROM THONG_BAO")
    ).mappings()
    for row in rows:
        title = TITLE_REPLACEMENTS.get(row["tieu_de"], row["tieu_de"])
        content = _normalize_content(row["noi_dung"])
        if title == row["tieu_de"] and content == row["noi_dung"]:
            continue
        bind.execute(
            text(
                "UPDATE THONG_BAO "
                "SET tieu_de = :title, noi_dung = :content "
                "WHERE Id_thong_bao = :notification_id"
            ),
            {
                "title": title,
                "content": content,
                "notification_id": row["Id_thong_bao"],
            },
        )


def _convert_tables(collation: str) -> None:
    if op.get_bind().dialect.name != "mysql":
        return
    existing_tables = _existing_tables()
    for table_name in TABLES:
        if table_name in existing_tables:
            op.execute(
                f"ALTER TABLE {table_name} "
                f"CONVERT TO CHARACTER SET utf8mb4 COLLATE {collation}"
            )


def upgrade() -> None:
    _convert_tables("utf8mb4_unicode_ci")
    if "THONG_BAO" in _existing_tables():
        _normalize_existing_notifications()


def downgrade() -> None:
    _convert_tables("utf8mb4_0900_ai_ci")
