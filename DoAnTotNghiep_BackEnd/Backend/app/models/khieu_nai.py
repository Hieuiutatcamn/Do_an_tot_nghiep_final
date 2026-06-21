from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class KhieuNai(Base):
    __tablename__ = "KHIEU_NAI"

    id_khieu_nai: Mapped[int] = mapped_column("Id_khieu_nai", primary_key=True, autoincrement=True)
    id_don_thue: Mapped[int | None] = mapped_column(ForeignKey("DON_THUE.Id_don_thue"))
    id_khach_hang: Mapped[int | None] = mapped_column(ForeignKey("KHACH_HANG.Id_khach_hang"))
    tieu_de: Mapped[str | None] = mapped_column(String(255))
    san_pham_khieu_nai: Mapped[str | None] = mapped_column(Text)
    noi_dung: Mapped[str | None] = mapped_column(Text)
    trang_thai: Mapped[str | None] = mapped_column(Unicode(50))
    ngay_khieu_nai: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)

    customer = relationship("KhachHang", back_populates="complaints")
    rental = relationship("DonThue", back_populates="complaints")
