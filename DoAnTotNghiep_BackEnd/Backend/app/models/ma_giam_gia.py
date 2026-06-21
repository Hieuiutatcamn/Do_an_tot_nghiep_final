from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Date, DateTime, Enum, Integer, String, Unicode, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.hang_so import (
    DIEU_KIEN_GIAM_GIA,
    TRANG_THAI_MA_GIAM_GIA,
    LOAI_GIAM_GIA,
)


class MaGiamGia(Base):
    __tablename__ = "MA_GIAM_GIA"

    id_ma_giam_gia: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ma_code: Mapped[str] = mapped_column("ma_giam_gia", String(50), unique=True, nullable=False)
    ten_ma: Mapped[str | None] = mapped_column(Unicode(255))
    mo_ta: Mapped[str | None] = mapped_column(Unicode(255))
    loai_giam_gia: Mapped[str] = mapped_column(Enum(*LOAI_GIAM_GIA, name="loai_giam_gia_ma"), nullable=False)
    gia_tri_giam: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    dieu_kien_loai: Mapped[str | None] = mapped_column(
        Enum(*DIEU_KIEN_GIAM_GIA, name="dieu_kien_ma_giam_gia"),
        default="khong_dieu_kien",
        server_default="khong_dieu_kien",
    )
    so_ngay_thue_toi_thieu: Mapped[int | None] = mapped_column(Integer, default=0, server_default="0")
    gia_tri_don_toi_thieu: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), default=0, server_default="0")
    ngay_bat_dau: Mapped[date | None] = mapped_column(Date)
    ngay_ket_thuc: Mapped[date | None] = mapped_column(Date)
    so_luong: Mapped[int | None] = mapped_column(Integer, default=0, server_default="0")
    da_su_dung: Mapped[int | None] = mapped_column(Integer, default=0, server_default="0")
    trang_thai: Mapped[str | None] = mapped_column(
        Enum(*TRANG_THAI_MA_GIAM_GIA, name="trang_thai_ma_giam_gia"),
        default="dang_hoat_dong",
        server_default="dang_hoat_dong",
    )
    created_at: Mapped[datetime | None] = mapped_column("ngay_tao", DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime | None] = mapped_column(
        "ngay_cap_nhat",
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    rentals = relationship("DonThue", back_populates="discount_code")
