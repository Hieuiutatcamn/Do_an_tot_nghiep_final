from datetime import date

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field

from app.schemas.tai_khoan import TaiKhoanPhanHoi
from app.schemas.chung import MoHinhORM


class KhachHangCoBan(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_tai_khoan: int | None = None
    ho_ten: str | None = Field(default=None, max_length=100)
    sdt: str | None = Field(default=None, max_length=20)
    gioi_tinh: str | None = Field(default=None, max_length=20)
    ngay_sinh: date | None = None
    dia_chi: str | None = Field(default=None, max_length=255)
    cccd: str | None = Field(default=None, max_length=20)
    so_cccd: str | None = Field(default=None, max_length=20)
    anh_cccd_mat_truoc: str | None = Field(default=None, max_length=255)
    anh_cccd_mat_sau: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(
        default=None,
        validation_alias=AliasChoices("email", "thu_dien_tu"),
    )


class KhachHangTao(KhachHangCoBan):
    ho_ten: str = Field(max_length=100, examples=["Nguyen Van A"])


class KhachHangCapNhat(KhachHangCoBan):
    pass


class KhachHangPhanHoi(MoHinhORM):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id_khach_hang: int
    id_tai_khoan: int | None = None
    ho_ten: str | None = None
    sdt: str | None = None
    gioi_tinh: str | None = None
    ngay_sinh: date | None = None
    dia_chi: str | None = None
    cccd: str | None = None
    so_cccd: str | None = None
    anh_cccd_mat_truoc: str | None = None
    anh_cccd_mat_sau: str | None = None
    email: EmailStr | None = Field(
        default=None,
        validation_alias=AliasChoices("email", "thu_dien_tu"),
    )
    account: TaiKhoanPhanHoi | None = None
