from datetime import date

from sqlalchemy import Date, ForeignKey, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database.base import Base


class KhachHang(Base):
    __tablename__ = "KHACH_HANG"

    id_khach_hang: Mapped[int] = mapped_column("Id_khach_hang", primary_key=True, autoincrement=True)
    id_tai_khoan: Mapped[int | None] = mapped_column("Id_tai_khoan", ForeignKey("TAI_KHOAN.id_tai_khoan"), unique=True)
    ho_ten: Mapped[str | None] = mapped_column(Unicode(100))
    sdt: Mapped[str | None] = mapped_column(String(20), unique=True)
    gioi_tinh: Mapped[str | None] = mapped_column(Unicode(20))
    ngay_sinh: Mapped[date | None] = mapped_column(Date)
    dia_chi: Mapped[str | None] = mapped_column(Unicode(255))
    so_cccd: Mapped[str | None] = mapped_column("So_CCCD", String(20), unique=True)
    anh_cccd_mat_truoc: Mapped[str | None] = mapped_column("Anh_CCCD_mat_truoc", String(255))
    anh_cccd_mat_sau: Mapped[str | None] = mapped_column("Anh_CCCD_mat_sau", String(255))
    thu_dien_tu: Mapped[str | None] = mapped_column("thu_dien_tu", String(100), unique=True)
    anh_cccd: Mapped[str | None] = mapped_column("Anh_CCCD", String(255))
    email = synonym("thu_dien_tu")

    account = relationship("TaiKhoan", back_populates="customer")
    cart_items = relationship("GioHang", back_populates="customer", cascade="all, delete-orphan")
    rentals = relationship("DonThue", back_populates="customer")
    chat_conversations = relationship("CuocTroChuyen", back_populates="customer")
    chat_tickets = relationship("PhieuChat", back_populates="customer")
    complaints = relationship("KhieuNai", back_populates="customer")

    @property
    def cccd(self) -> str | None:
        return self.so_cccd

    @cccd.setter
    def cccd(self, value: str | None) -> None:
        self.so_cccd = value
