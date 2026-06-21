from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LoaiThongBao = Literal[
    "Dat hang thanh cong",
    "Co don hang moi",
    "Cap nhat don hang",
    "Khieu nai",
    "He thong",
]
NguoiNhanThongBao = Literal["User", "Admin", "Nhan vien"]
TrangThaiThongBao = Literal["Chua doc", "Da doc"]


class ThongBaoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ThongBaoTao(ThongBaoSchema):
    id_tai_khoan: int | None = Field(default=None, alias="Id_tai_khoan")
    id_don_thue: int | None = Field(default=None, alias="Id_don_thue")
    tieu_de: str = Field(max_length=100)
    noi_dung: str = Field(max_length=255)
    loai_thong_bao: LoaiThongBao
    doi_tuong_nhan: NguoiNhanThongBao


class ThongBaoPhanHoi(ThongBaoSchema):
    id_thong_bao: int = Field(alias="Id_thong_bao")
    id_tai_khoan: int | None = Field(default=None, alias="Id_tai_khoan")
    id_don_thue: int | None = Field(default=None, alias="Id_don_thue")
    tieu_de: str | None = None
    noi_dung: str | None = None
    loai_thong_bao: str | None = None
    doi_tuong_nhan: str | None = None
    trang_thai: str | None = None
    ngay_tao: datetime | None = None
    ten_khach_hang: str | None = None


class DemThongBaoChuaDocPhanHoi(BaseModel):
    dem_thong_bao_chua_doc: int


class CapNhatNhieuThongBaoPhanHoi(BaseModel):
    updated: int
