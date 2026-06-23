from datetime import date

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class DangKyYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(
        validation_alias=AliasChoices("username", "ten_dang_nhap"),
        min_length=3,
        max_length=50,
        examples=["kh16"],
    )
    password: str = Field(
        validation_alias=AliasChoices("password", "mat_khau"),
        min_length=6,
        max_length=72,
        examples=["123456"],
    )
    ho_ten: str = Field(max_length=100, examples=["Nguyen Van A"])
    sdt: str | None = Field(default=None, max_length=20, examples=["0912345678"])
    cccd: str | None = Field(default=None, max_length=20, examples=["001001000099"])
    email: EmailStr | None = Field(
        default=None,
        validation_alias=AliasChoices("email", "thu_dien_tu"),
        examples=["customer@example.com"],
    )
    so_cccd: str | None = Field(default=None, max_length=20, examples=["001001000099"])
    anh_cccd_mat_truoc: str | None = None
    anh_cccd_mat_sau: str | None = None


class DangNhapYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(validation_alias=AliasChoices("username", "ten_dang_nhap"), examples=["kh01"])
    password: str = Field(validation_alias=AliasChoices("password", "mat_khau"), examples=["123456"])


class LamMoiTokenYeuCau(BaseModel):
    refresh_token: str


class DoiMatKhauYeuCau(BaseModel):
    mat_khau_hien_tai: str = Field(min_length=1, max_length=72)
    mat_khau_moi: str = Field(min_length=6, max_length=72)


class QuenMatKhauYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr = Field(validation_alias=AliasChoices("email", "thu_dien_tu"))


class DatLaiMatKhauYeuCau(BaseModel):
    token: str = Field(min_length=1)
    mat_khau_moi: str = Field(min_length=6, max_length=72)


class DoiMatKhauPhanHoi(BaseModel):
    message: str


class TokenPhanHoi(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TaiKhoanPhanHoi(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tai_khoan: int
    dang_nhap: str
    vai_tro: str | None = None
    trang_thai: str | None = None
    nha_cung_cap: str | None = None
    nha_cung_cap_id: str | None = None
    anh_dai_dien: str | None = None


class HoSoKhachHangPhanHoi(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_khach_hang: int
    id_tai_khoan: int | None = None
    ho_ten: str | None = None
    sdt: str | None = None
    gioi_tinh: str | None = None
    ngay_sinh: date | None = None
    dia_chi: str | None = None
    cccd: str | None = None
    so_cccd: str | None = None
    email: EmailStr | None = Field(
        default=None,
        validation_alias=AliasChoices("email", "thu_dien_tu"),
    )
    anh_cccd_mat_truoc: str | None = None
    anh_cccd_mat_sau: str | None = None


class ToiPhanHoi(BaseModel):
    account: TaiKhoanPhanHoi
    customer: HoSoKhachHangPhanHoi | None = None
    id: int | None = None
    ho_ten: str | None = None
    email: EmailStr | None = None
    anh_dai_dien: str | None = None
    nha_cung_cap: str | None = None
