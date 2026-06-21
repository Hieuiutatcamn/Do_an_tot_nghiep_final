from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.chung import MoHinhORM


class GuiTroChuyenYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("conversation_id", "id_cuoc_tro_chuyen"),
    )
    message: str = Field(
        validation_alias=AliasChoices("message", "noi_dung_tin_nhan", "noi_dung"),
        min_length=1,
        examples=["Tu van giup toi may chup chan dung"],
    )


class NhanVienChatYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_khach_hang: int | None = None
    conversation_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("conversation_id", "id_cuoc_tro_chuyen"),
    )
    # Loai yeu cau do chatbot AI phan loai (KHIEU_NAI/HUY_DON/HOAN_TIEN/CAN_XAC_NHAN/KHAC)
    loai_yeu_cau: str | None = Field(
        default=None,
        validation_alias=AliasChoices("loai_yeu_cau", "ticket_type", "category"),
    )


class TinNhanNhanVienYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("conversation_id", "id_cuoc_tro_chuyen"),
    )
    message: str = Field(
        validation_alias=AliasChoices("message", "noi_dung_tin_nhan", "noi_dung"),
        min_length=1,
        examples=["Toi can nhan vien ho tro don hang"],
    )


class AdminTraLoiNhanVienYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: int = Field(
        validation_alias=AliasChoices("conversation_id", "id_cuoc_tro_chuyen"),
    )
    message: str = Field(
        validation_alias=AliasChoices("message", "noi_dung_tin_nhan", "noi_dung"),
        min_length=1,
        examples=["SunLens xin chao, minh co the ho tro gi cho ban?"],
    )


class NhanVienOnlineYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    is_online: bool = Field(
        default=True,
        validation_alias=AliasChoices("is_online", "dang_truc_tuyen"),
    )


class TinNhanTroChuyenPhanHoi(MoHinhORM):
    id_tin_nhan: int
    id_cuoc_tro_chuyen: int
    sender_type: Literal["CUSTOMER", "STAFF"]
    sender_id: int | None = None
    noi_dung: str
    loai_tin_nhan: str | None = "TEXT"
    da_doc: bool | None = False
    created_at: datetime | None = None


class CuocTroChuyenPhanHoi(MoHinhORM):
    id_cuoc_tro_chuyen: int
    id_khach_hang: int
    id_nhan_vien: int | None = None
    chat_mode: Literal["STAFF"]
    trang_thai: Literal["CHO_NHAN_VIEN", "NHAN_VIEN_DANG_XU_LY", "DA_DONG"]
    chu_de: str | None = None
    need_staff: bool | None = False
    can_nhan_vien: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    customer_name: str | None = None
    employee_name: str | None = None
    last_message: str | None = None
    waiting_count: int | None = None
    unread_customer_count: int | None = None
    so_tin_nhan_khach_chua_doc: int | None = None


class GuiTroChuyenPhanHoi(BaseModel):
    success: bool = True
    staff_online: bool | None = None
    message: str
    ticket_id: int | None = None
    conversation: CuocTroChuyenPhanHoi
    user_message: TinNhanTroChuyenPhanHoi | None = None
    reply_message: TinNhanTroChuyenPhanHoi | None = None
    messages: list[TinNhanTroChuyenPhanHoi] = Field(default_factory=list)


class TrangThaiNhanVienPhanHoi(BaseModel):
    staff_online: bool
    online: bool
    message: str


class DanhSachCuocTroChuyenAdminPhanHoi(BaseModel):
    items: list[CuocTroChuyenPhanHoi]
    waiting_count: int = 0
    unread_message_count: int = 0


class LuuTinNhanAIYeuCau(BaseModel):
    """Luu 1 tin nhan vao lich su chat AI cua khach da dang nhap."""

    model_config = ConfigDict(populate_by_name=True)

    vai_tro: Literal["USER", "AI"] = "USER"
    noi_dung: str = Field(
        min_length=1,
        validation_alias=AliasChoices("noi_dung", "message", "noi_dung_tin_nhan"),
    )


class TinNhanAIPhanHoi(MoHinhORM):
    id_tin_nhan_ai: int
    vai_tro: str
    noi_dung: str
    created_at: datetime | None = None
