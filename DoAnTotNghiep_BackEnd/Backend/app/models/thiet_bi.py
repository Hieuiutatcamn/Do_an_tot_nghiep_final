from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey, Integer, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ThietBi(Base):
    __tablename__ = "THIET_BI"
    id_thiet_bi: Mapped[int] = mapped_column("Id_thiet_bi", primary_key=True, autoincrement=True)
    ten_thiet_bi: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    danh_muc_id: Mapped[int | None] = mapped_column("id_danh_muc", ForeignKey("DANH_MUC.Id_danh_muc"))
    so_luong: Mapped[int | None] = mapped_column(Integer, default=0)
    gia_thue: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2))
    tinh_trang: Mapped[str | None] = mapped_column(Unicode(50))
    mo_ta: Mapped[str | None] = mapped_column(Unicode(255))
    hinh_anh: Mapped[str | None] = mapped_column(String(2000))
    category = relationship("DanhMuc", back_populates="devices")
    cart_items = relationship("GioHang", back_populates="device")
    rental_details = relationship("ChiTietDonThue", back_populates="device")
