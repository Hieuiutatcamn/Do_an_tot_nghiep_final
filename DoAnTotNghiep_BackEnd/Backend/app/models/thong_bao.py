from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Unicode, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.hang_so import (
    LUA_CHON_NGUOI_NHAN_THONG_BAO,
    TRANG_THAI_THONG_BAO,
    LUA_CHON_LOAI_THONG_BAO,
)


class ThongBao(Base):
    __tablename__ = "THONG_BAO"

    id_thong_bao: Mapped[int] = mapped_column("Id_thong_bao", primary_key=True, autoincrement=True)
    id_tai_khoan: Mapped[int | None] = mapped_column(
        "Id_tai_khoan",
        ForeignKey("TAI_KHOAN.id_tai_khoan"),
    )
    id_don_thue: Mapped[int | None] = mapped_column(
        "Id_don_thue",
        ForeignKey("DON_THUE.Id_don_thue"),
    )
    tieu_de: Mapped[str | None] = mapped_column(Unicode(100))
    noi_dung: Mapped[str | None] = mapped_column(Unicode(255))
    loai_thong_bao: Mapped[str | None] = mapped_column(
        Enum(*LUA_CHON_LOAI_THONG_BAO, name="loai_thong_bao"),
    )
    doi_tuong_nhan: Mapped[str | None] = mapped_column(
        Enum(*LUA_CHON_NGUOI_NHAN_THONG_BAO, name="doi_tuong_nhan"),
    )
    trang_thai: Mapped[str | None] = mapped_column(
        Enum(*TRANG_THAI_THONG_BAO, name="trang_thai_thong_bao"),
        default="Chua doc",
        server_default="Chua doc",
    )
    ngay_tao: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.current_timestamp())

    account = relationship("TaiKhoan", back_populates="notifications")
    rental = relationship("DonThue", back_populates="notifications")
