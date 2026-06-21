from pydantic import BaseModel, Field

from app.schemas.tai_khoan import TaiKhoanPhanHoi
from app.schemas.chung import MoHinhORM


class NhanVienCoBan(BaseModel):
    id_tai_khoan: int | None = None
    ho_ten: str | None = Field(default=None, max_length=100)
    sdt: str | None = Field(default=None, max_length=20)


class NhanVienTao(NhanVienCoBan):
    ho_ten: str = Field(max_length=100, examples=["Le Van Nam"])


class NhanVienCapNhat(NhanVienCoBan):
    pass


class NhanVienPhanHoi(MoHinhORM):
    id_nhan_vien: int
    id_tai_khoan: int | None = None
    ho_ten: str | None = None
    sdt: str | None = None
    account: TaiKhoanPhanHoi | None = None
