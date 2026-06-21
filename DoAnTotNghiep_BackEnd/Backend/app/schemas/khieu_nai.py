from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.chung import MoHinhORM

DANH_SACH_TRANG_THAI_KHIEU_NAI = (
    "Cho phan hoi",
    "Dang xu ly",
    "Da xu ly",
    "Chờ xử lý",
    "Đang xử lý",
    "Đã tiếp nhận",
    "Chờ phản hồi",
    "Đã xử lý",
)


class KhieuNaiTao(BaseModel):
    id_don_thue: int | None = None
    id_thiet_bi_list: list[int] = Field(default_factory=list)
    tieu_de: str | None = Field(default=None, max_length=255)
    noi_dung: str = Field(min_length=1, max_length=1000)

    @field_validator("tieu_de", "noi_dung")
    @classmethod
    def validate_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Không được để trống")
        return value


class KhieuNaiCapNhat(BaseModel):
    id_don_thue: int | None = None
    id_khach_hang: int | None = None
    tieu_de: str | None = Field(default=None, max_length=255)
    san_pham_khieu_nai: str | None = None
    noi_dung: str | None = Field(default=None, max_length=1000)
    trang_thai: str | None = Field(default=None, max_length=50)


class TrangThaiKhieuNaiCapNhat(BaseModel):
    trang_thai: str = Field(max_length=50, examples=["Đang xử lý"])


class KhieuNaiTaoPhanHoi(BaseModel):
    message: str
    id_khieu_nai: int
    trang_thai: str | None = None
    tieu_de: str | None = None
    noi_dung: str | None = None


class KhieuNaiPhanHoi(MoHinhORM):
    id_khieu_nai: int
    id_don_thue: int | None = None
    id_khach_hang: int | None = None
    tieu_de: str | None = None
    san_pham_khieu_nai: str | None = None
    noi_dung: str | None = None
    trang_thai: str | None = None
    ngay_khieu_nai: datetime | None = None


class MotKhieuNaiCuaToiPhanHoi(BaseModel):
    Id_khieu_nai: int
    id_khieu_nai: int
    id_don_thue: int | None = None
    ma_don: str | None = None
    san_pham_khieu_nai: str | None = None
    tieu_de: str | None = None
    noi_dung: str | None = None
    trang_thai: str | None = None
    ngay_khieu_nai: datetime | None = None


class KhieuNaiCuaToiPhanHoi(BaseModel):
    items: list[MotKhieuNaiCuaToiPhanHoi]


class KhieuNaiAdminPhanHoi(BaseModel):
    Id_khieu_nai: int
    id_khieu_nai: int
    id_don_thue: int | None = None
    ma_don: str | None = None
    id_khach_hang: int | None = None
    ten_khach_hang: str | None = None
    sdt: str | None = None
    tieu_de: str | None = None
    san_pham_khieu_nai: str | None = None
    noi_dung: str | None = None
    trang_thai: str | None = None
    ngay_khieu_nai: datetime | None = None
