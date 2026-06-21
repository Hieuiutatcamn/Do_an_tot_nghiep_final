from sqlalchemy import Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DanhMuc(Base):
    __tablename__ = "DANH_MUC"

    id_danh_muc: Mapped[int] = mapped_column("Id_danh_muc", primary_key=True, autoincrement=True)
    ten_danh_muc: Mapped[str | None] = mapped_column(Unicode(100))
    mo_ta: Mapped[str | None] = mapped_column(Unicode(255))

    devices = relationship("ThietBi", back_populates="category")
