from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.hang_so import (
    TRANG_THAI_TRO_CHUYEN,
    LOAI_TIN_NHAN,
    CHON_NGUOI_CHAT,
    CHON_NGUOI_GUI_TIN_NHAN,
    TRANG_THAI_VE_CHAT,
    LOAI_VE_CHAT,
    CHON_VAI_TRO_AI,
)


class CuocTroChuyen(Base):
    __tablename__ = "cuoc_tro_chuyen"

    id_cuoc_tro_chuyen: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_khach_hang: Mapped[int] = mapped_column(ForeignKey("KHACH_HANG.Id_khach_hang"), nullable=False)
    id_nhan_vien: Mapped[int | None] = mapped_column(ForeignKey("NHAN_VIEN.Id_nhan_vien"))
    chat_mode: Mapped[str] = mapped_column(
        "che_do_chat",
        Enum(*CHON_NGUOI_CHAT, name="chat_mode"),
        default="STAFF",
        server_default="STAFF",
        nullable=False,
    )
    trang_thai: Mapped[str] = mapped_column(
        Enum(*TRANG_THAI_TRO_CHUYEN, name="trang_thai_cuoc_tro_chuyen"),
        default="CHO_NHAN_VIEN",
        server_default="CHO_NHAN_VIEN",
        nullable=False,
    )
    chu_de: Mapped[str | None] = mapped_column(String(255))
    need_staff: Mapped[bool] = mapped_column("can_nhan_vien", Boolean, default=False, server_default="0")
    created_at: Mapped[datetime | None] = mapped_column("ngay_tao", DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime | None] = mapped_column(
        "ngay_cap_nhat",
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    customer = relationship("KhachHang", back_populates="chat_conversations")
    employee = relationship("NhanVien", back_populates="chat_conversations")
    messages = relationship(
        "TinNhanCuocTroChuyen",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    tickets = relationship("PhieuChat", back_populates="conversation", cascade="all, delete-orphan")


class TinNhanCuocTroChuyen(Base):
    __tablename__ = "tin_nhan_chat"

    id_tin_nhan: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cuoc_tro_chuyen: Mapped[int] = mapped_column(
        ForeignKey("cuoc_tro_chuyen.id_cuoc_tro_chuyen"),
        nullable=False,
    )
    sender_type: Mapped[str] = mapped_column(
        "loai_nguoi_gui",
        Enum(*CHON_NGUOI_GUI_TIN_NHAN, name="sender_type_chat"),
        nullable=False,
    )
    sender_id: Mapped[int | None] = mapped_column("id_nguoi_gui", Integer)
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    loai_tin_nhan: Mapped[str] = mapped_column(
        Enum(*LOAI_TIN_NHAN, name="loai_tin_nhan_chat"),
        default="TEXT",
        server_default="TEXT",
    )
    da_doc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime | None] = mapped_column("ngay_tao", DateTime, server_default=func.current_timestamp())

    conversation = relationship("CuocTroChuyen", back_populates="messages")


class NhanVienOnline(Base):
    __tablename__ = "nhan_vien_online"

    id: Mapped[int] = mapped_column("id_nhan_vien_online", primary_key=True, autoincrement=True)
    id_nhan_vien: Mapped[int] = mapped_column(
        ForeignKey("NHAN_VIEN.Id_nhan_vien"),
        nullable=False,
        unique=True,
    )
    is_online: Mapped[bool] = mapped_column("dang_truc_tuyen", Boolean, default=False, server_default="0")
    last_seen: Mapped[datetime | None] = mapped_column(
        "lan_cuoi_hoat_dong",
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    employee = relationship("NhanVien", back_populates="online_status")


class PhieuChat(Base):
    __tablename__ = "chat_ticket"

    id_ticket: Mapped[int] = mapped_column("id_yeu_cau_chat", primary_key=True, autoincrement=True)
    id_cuoc_tro_chuyen: Mapped[int] = mapped_column(
        ForeignKey("cuoc_tro_chuyen.id_cuoc_tro_chuyen"),
        nullable=False,
    )
    id_khach_hang: Mapped[int] = mapped_column(ForeignKey("KHACH_HANG.Id_khach_hang"), nullable=False)
    loai_ticket: Mapped[str] = mapped_column(
        "loai_yeu_cau",
        Enum(*LOAI_VE_CHAT, name="loai_chat_ticket"),
        default="KHAC",
        server_default="KHAC",
    )
    noi_dung: Mapped[str | None] = mapped_column(Text)
    trang_thai: Mapped[str] = mapped_column(
        Enum(*TRANG_THAI_VE_CHAT, name="trang_thai_chat_ticket"),
        default="MOI",
        server_default="MOI",
    )
    created_at: Mapped[datetime | None] = mapped_column("ngay_tao", DateTime, server_default=func.current_timestamp())

    conversation = relationship("CuocTroChuyen", back_populates="tickets")
    customer = relationship("KhachHang", back_populates="chat_tickets")


class TinNhanAI(Base):
    """Lich su tro chuyen voi chatbot AI cua khach DA DANG NHAP (khach vang lai luu localStorage)."""

    __tablename__ = "tin_nhan_ai"

    id_tin_nhan_ai: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_khach_hang: Mapped[int] = mapped_column(ForeignKey("KHACH_HANG.Id_khach_hang"), nullable=False)
    vai_tro: Mapped[str] = mapped_column(
        Enum(*CHON_VAI_TRO_AI, name="vai_tro_tin_nhan_ai"),
        nullable=False,
    )
    noi_dung: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column("ngay_tao", DateTime, server_default=func.current_timestamp())
