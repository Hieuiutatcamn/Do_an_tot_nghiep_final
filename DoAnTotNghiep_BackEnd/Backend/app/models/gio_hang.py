from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GioHang(Base):
    __tablename__ = "GIO_HANG"

    id_gio_hang: Mapped[int] = mapped_column("Id_gio_hang", primary_key=True, autoincrement=True)
    id_khach_hang: Mapped[int] = mapped_column(
        "Id_khach_hang",
        ForeignKey("KHACH_HANG.Id_khach_hang"),
        nullable=False,
    )
    id_thiet_bi: Mapped[int] = mapped_column(
        "Id_thiet_bi",
        ForeignKey("THIET_BI.Id_thiet_bi"),
        nullable=False,
    )
    so_luong: Mapped[int | None] = mapped_column(Integer, default=1, server_default=text("1"))
    ngay_nhan: Mapped[date | None] = mapped_column(Date)
    ngay_tra: Mapped[date | None] = mapped_column(Date)
    ngay_them: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.current_timestamp())

    customer = relationship("KhachHang", back_populates="cart_items")
    device = relationship("ThietBi", back_populates="cart_items")
