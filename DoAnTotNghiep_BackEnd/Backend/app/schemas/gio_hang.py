from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

NGAY_NHAN_QUA_KHU_ERROR = "Ngày nhận không được nhỏ hơn ngày hiện tại."
NGAY_TRA_KHONG_HOP_LE_ERROR = "Ngày trả phải lớn hơn ngày nhận."


class GioHangSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class MucGioHangTao(GioHangSchema):
    id_thiet_bi: int = Field(alias="Id_thiet_bi", gt=0)
    so_luong: int = Field(default=1, gt=0)
    ngay_nhan: date
    ngay_tra: date

    @model_validator(mode="after")
    def validate_date_range(self) -> "MucGioHangTao":
        if self.ngay_nhan < date.today():
            raise ValueError(NGAY_NHAN_QUA_KHU_ERROR)
        if self.ngay_tra <= self.ngay_nhan:
            raise ValueError(NGAY_TRA_KHONG_HOP_LE_ERROR)
        return self


class MucGioHangCapNhat(GioHangSchema):
    so_luong: int | None = Field(default=None, gt=0)
    ngay_nhan: date | None = None
    ngay_tra: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "MucGioHangCapNhat":
        if self.ngay_nhan is not None and self.ngay_nhan < date.today():
            raise ValueError(NGAY_NHAN_QUA_KHU_ERROR)
        if self.ngay_nhan is not None and self.ngay_tra is not None and self.ngay_tra <= self.ngay_nhan:
            raise ValueError(NGAY_TRA_KHONG_HOP_LE_ERROR)
        return self


class MucGioHangPhanHoi(GioHangSchema):
    id_gio_hang: int = Field(alias="Id_gio_hang")
    id_thiet_bi: int = Field(alias="Id_thiet_bi")
    ten_thiet_bi: str | None = None
    hinh_anh: str | None = None
    trang_thai: str | None = None
    ngay_nhan: date | None = None
    ngay_tra: date | None = None
    so_ngay_thue: int
    gia_thue: int
    so_luong: int
    thanh_tien: int


class GioHangPhanHoi(BaseModel):
    items: list[MucGioHangPhanHoi]
    tong_san_pham: int
    tong_so_ngay_thue: int
    tong_tien_thue: int
