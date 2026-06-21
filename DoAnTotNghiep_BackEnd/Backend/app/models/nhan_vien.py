from sqlalchemy import ForeignKey, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class NhanVien(Base):
    __tablename__ = "NHAN_VIEN"

    id_nhan_vien: Mapped[int] = mapped_column("Id_nhan_vien", primary_key=True, autoincrement=True)
    id_tai_khoan: Mapped[int | None] = mapped_column("Id_tai_khoan", ForeignKey("TAI_KHOAN.id_tai_khoan"), unique=True)
    ho_ten: Mapped[str | None] = mapped_column(Unicode(100))
    sdt: Mapped[str | None] = mapped_column(Unicode(20))

    account = relationship("TaiKhoan", back_populates="employee")
    chat_conversations = relationship("CuocTroChuyen", back_populates="employee")
    online_status = relationship("NhanVienOnline", back_populates="employee", uselist=False)
