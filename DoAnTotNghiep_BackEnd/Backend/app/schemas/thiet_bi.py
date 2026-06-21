from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.danh_muc import DanhMucPhanHoi
from app.schemas.chung import MoHinhTienTe


class ThietBiCoBan(BaseModel):
    ten_thiet_bi: str | None = Field(default=None, max_length=100)
    danh_muc_id: int | None = None
    so_luong: int | None = Field(default=0, ge=0)
    gia_thue: Decimal | None = Field(default=None, ge=0)
    tinh_trang: str | None = Field(default=None, max_length=50)
    mo_ta: str | None = Field(default=None, max_length=255)
    hinh_anh: str | None = Field(default=None, max_length=2000)


class ThietBiTao(ThietBiCoBan):
    ten_thiet_bi: str = Field(max_length=100, examples=["Sony A7IV"])
    so_luong: int = Field(default=0, ge=0)
    gia_thue: Decimal = Field(ge=0, examples=[750000])


class ThietBiCapNhat(ThietBiCoBan):
    pass


class ThietBiPhanHoi(MoHinhTienTe):
    id_thiet_bi: int
    ten_thiet_bi: str
    danh_muc_id: int | None = None
    so_luong: int | None = None
    gia_thue: Decimal | None = None
    tinh_trang: str | None = None
    mo_ta: str | None = None
    hinh_anh: str | None = None
    category: DanhMucPhanHoi | None = None


class ThietBiKhaDungPhanHoi(ThietBiPhanHoi):
    tong_so_luong: int
    so_luong_da_dat: int
    so_luong_kha_dung: int
    available: bool = True


class KhaDungThietBiPhanHoi(BaseModel):
    Id_thiet_bi: int
    id_thiet_bi: int
    ten_thiet_bi: str
    tong_so_luong: int
    so_luong_da_dat: int
    so_luong_kha_dung: int
    remaining_quantity: int
    available: bool
    so_luong: int
    con_hang: bool
    message: str
    tinh_trang: str | None = None
