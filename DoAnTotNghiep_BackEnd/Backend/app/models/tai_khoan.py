from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import BitBoolean


class TaiKhoan(Base):
    __tablename__ = "TAI_KHOAN"
    __table_args__ = (
        UniqueConstraint("nha_cung_cap", "id_nha_cung_cap", name="uq_tai_khoan_nha_cung_cap_identity"),
    )

    id_tai_khoan: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dang_nhap: Mapped[str] = mapped_column("Dang_nhap", String(50), nullable=False, unique=True)
    mat_khau: Mapped[str] = mapped_column("Mat_khau", String(100), nullable=False)
    vai_tro: Mapped[str | None] = mapped_column("Vai_tro", String(20))
    trang_thai: Mapped[str | None] = mapped_column("Trang_thai", String(20))
    key: Mapped[bool | None] = mapped_column("kich_hoat", BitBoolean())
    nha_cung_cap: Mapped[str | None] = mapped_column("nha_cung_cap", String(20), default="local", server_default="local")
    nha_cung_cap_id: Mapped[str | None] = mapped_column("id_nha_cung_cap", String(255))
    anh_dai_dien: Mapped[str | None] = mapped_column("anh_dai_dien", String(500))

    customer = relationship("KhachHang", back_populates="account", uselist=False)
    employee = relationship("NhanVien", back_populates="account", uselist=False)
    notifications = relationship("ThongBao", back_populates="account")
