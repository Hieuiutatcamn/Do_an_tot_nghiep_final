from pydantic import BaseModel, Field

from app.schemas.chung import MoHinhORM


class TaiKhoanCoBan(BaseModel):
    dang_nhap: str | None = Field(default=None, min_length=3, max_length=50)
    vai_tro: str | None = Field(default=None, max_length=20, examples=["Khach hang"])
    trang_thai: str | None = Field(default=None, max_length=20, examples=["Hoat dong"])
    key: bool | None = Field(default=True)
    nha_cung_cap: str | None = Field(default=None, max_length=20)
    nha_cung_cap_id: str | None = Field(default=None, max_length=255)
    anh_dai_dien: str | None = Field(default=None, max_length=500)


class TaiKhoanTao(TaiKhoanCoBan):
    dang_nhap: str = Field(min_length=3, max_length=50, examples=["nv04"])
    mat_khau: str = Field(min_length=6, max_length=72, examples=["123456"])


class TaiKhoanCapNhat(TaiKhoanCoBan):
    pass


class TaiKhoanCapNhatMatKhau(BaseModel):
    mat_khau: str = Field(min_length=6, max_length=72, examples=["new123456"])


class TaiKhoanPhanHoi(MoHinhORM):
    id_tai_khoan: int
    dang_nhap: str
    vai_tro: str | None = None
    trang_thai: str | None = None
    key: bool | None = None
    nha_cung_cap: str | None = None
    nha_cung_cap_id: str | None = None
    anh_dai_dien: str | None = None
