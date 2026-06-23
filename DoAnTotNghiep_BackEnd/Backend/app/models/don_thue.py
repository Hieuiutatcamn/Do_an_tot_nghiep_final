from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, DateTime, Enum, ForeignKey, Integer, String, Unicode, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.hang_so import TRANG_THAI_DON_HANG

class DonThue(Base):
    __tablename__ = "DON_THUE"

    id_don_thue: Mapped[int] = mapped_column("Id_don_thue", primary_key=True, autoincrement=True)
    id_khach_hang: Mapped[int | None] = mapped_column("Id_khach_hang", ForeignKey("KHACH_HANG.Id_khach_hang"))
    ngay_dat: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.current_timestamp())
    trang_thai: Mapped[str | None] = mapped_column(Unicode(50), default="Da dat", server_default="Da dat")
    tong_tien: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), default=0)
    id_ma_giam_gia: Mapped[int | None] = mapped_column(ForeignKey("MA_GIAM_GIA.id_ma_giam_gia"))
    so_tien_giam: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), default=0, server_default="0")
    anh_chuyen_khoan: Mapped[str | None] = mapped_column("Anh_chuyen_khoan", String(255))
    phuong_thuc_thanh_toan: Mapped[str | None] = mapped_column(Unicode(50))
    ma_giao_dich_vnpay: Mapped[str | None] = mapped_column(String(100))
    so_tien_da_thanh_toan: Mapped[Decimal | None] = mapped_column(
        DECIMAL(12, 2),
        default=0,
        server_default="0",
    )
    han_thanh_toan_vnpay: Mapped[datetime | None] = mapped_column(DateTime)
    ngay_thanh_toan: Mapped[datetime | None] = mapped_column(DateTime)
    ghi_chu: Mapped[str | None] = mapped_column(Unicode(255))

    customer = relationship("KhachHang", back_populates="rentals")
    discount_code = relationship("MaGiamGia", back_populates="rentals")
    notifications = relationship("ThongBao", back_populates="rental")
    details = relationship(
        "ChiTietDonThue",
        back_populates="rental",
        cascade="all, delete-orphan",
    )
    complaints = relationship("KhieuNai", back_populates="rental")


class ChiTietDonThue(Base):
    __tablename__ = "CHI_TIET_DON_THUE"

    id_chi_tiet_don_thue: Mapped[int] = mapped_column(
        "Id_chi_tiet_don_thue",
        primary_key=True,
        autoincrement=True,
    )
    id_don_thue: Mapped[int | None] = mapped_column(ForeignKey("DON_THUE.Id_don_thue"))
    id_thiet_bi: Mapped[int | None] = mapped_column(ForeignKey("THIET_BI.Id_thiet_bi"))
    ngay_nhan: Mapped[datetime | None] = mapped_column(DateTime)
    ngay_tra: Mapped[datetime | None] = mapped_column(DateTime)
    so_luong: Mapped[int | None] = mapped_column(Integer)
    gia_thue: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    trang_thai: Mapped[str | None] = mapped_column(
        Enum(*TRANG_THAI_DON_HANG, name="trang_thai_chi_tiet_don_thue"),
        default="Da dat",
        server_default="Da dat",
    )

    rental = relationship("DonThue", back_populates="details")
    device = relationship("ThietBi", back_populates="rental_details")
