from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class TaoThanhToanVnpayYeuCau(BaseModel):
    id_don_thue: int = Field(gt=0)
    so_tien: Decimal = Field(gt=0)
    noi_dung_thanh_toan: str = Field(min_length=1, max_length=255)


class TaoThanhToanVnpayPhanHoi(BaseModel):
    thanh_cong: bool
    duong_dan_thanh_toan: str


class KetQuaThanhToanVnpayPhanHoi(BaseModel):
    thanh_cong: bool
    chu_ky_hop_le: bool
    thong_bao: str
    id_don_thue: int | None = None
    so_tien: Decimal | None = None
    ma_giao_dich: str | None = None
    ma_phan_hoi: str | None = None
    trang_thai_giao_dich: str | None = None
    ngay_thanh_toan: datetime | None = None
    da_cap_nhat_he_thong: bool = False
