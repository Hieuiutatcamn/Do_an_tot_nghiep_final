from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.chung import MoHinhTienTe

LoaiGiamGia = Literal["phan_tram", "tien_mat"]
DieuKienGiamGia = Literal["so_ngay_thue", "tong_tien_don", "khong_dieu_kien"]
TrangThaiGiamGia = Literal["dang_hoat_dong", "tam_ngung", "het_han"]


class MaGiamGiaCoBan(BaseModel):
    ma_code: str | None = Field(default=None, max_length=50)
    ten_ma: str | None = Field(default=None, max_length=255)
    mo_ta: str | None = Field(default=None, max_length=255)
    loai_giam_gia: LoaiGiamGia | None = None
    gia_tri_giam: Decimal | None = Field(default=None, ge=0)
    dieu_kien_loai: DieuKienGiamGia | None = "khong_dieu_kien"
    so_ngay_thue_toi_thieu: int | None = Field(default=0, ge=0)
    gia_tri_don_toi_thieu: Decimal | None = Field(default=0, ge=0)
    ngay_bat_dau: date | None = None
    ngay_ket_thuc: date | None = None
    so_luong: int | None = Field(default=0, ge=0)
    trang_thai: TrangThaiGiamGia | None = "dang_hoat_dong"

    @field_validator("ma_code")
    @classmethod
    def uppercase_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().upper()
        if not value:
            raise ValueError("Mã giảm giá không được trống")
        return value

    @field_validator("ten_ma", "mo_ta")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_discount(self) -> "MaGiamGiaCoBan":
        if self.loai_giam_gia == "phan_tram" and self.gia_tri_giam is not None:
            if self.gia_tri_giam <= 0 or self.gia_tri_giam > 100:
                raise ValueError("Loại phần trăm chỉ cho nhập từ 1 đến 100")
        if self.loai_giam_gia == "tien_mat" and self.gia_tri_giam is not None and self.gia_tri_giam <= 0:
            raise ValueError("Giá trị giảm tiền mặt phải lớn hơn 0")
        if self.ngay_bat_dau and self.ngay_ket_thuc and self.ngay_ket_thuc < self.ngay_bat_dau:
            raise ValueError("Ngày kết thúc không được nhỏ hơn ngày bắt đầu")
        if self.dieu_kien_loai == "so_ngay_thue" and not self.so_ngay_thue_toi_thieu:
            raise ValueError("Vui lòng nhập số ngày thuê tối thiểu")
        if self.dieu_kien_loai == "tong_tien_don" and not self.gia_tri_don_toi_thieu:
            raise ValueError("Vui lòng nhập tổng tiền đơn tối thiểu")
        return self


class MaGiamGiaTao(MaGiamGiaCoBan):
    ma_code: str = Field(max_length=50)
    loai_giam_gia: LoaiGiamGia
    gia_tri_giam: Decimal = Field(gt=0)


class MaGiamGiaCapNhat(MaGiamGiaCoBan):
    pass


class TrangThaiMaGiamGiaCapNhat(BaseModel):
    trang_thai: TrangThaiGiamGia


class ApDungMaGiamGiaYeuCau(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ma_code: str = Field(
        validation_alias=AliasChoices("ma_code", "ma_giam_gia", "code", "discountCode"),
        min_length=1,
        max_length=50,
    )
    tong_tien: Decimal = Field(ge=0)
    so_ngay_thue: int = Field(ge=0)

    @field_validator("ma_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class ApDungMaGiamGiaPhanHoi(MoHinhTienTe):
    valid: bool
    message: str
    id_ma_giam_gia: int | None = None
    ma_code: str | None = None
    loai_giam_gia: str | None = None
    gia_tri_giam: Decimal | None = None
    so_tien_giam: Decimal = Decimal("0")
    tong_tien_sau_giam: Decimal


class MaGiamGiaPhanHoi(MoHinhTienTe):
    id_ma_giam_gia: int
    ma_code: str
    ten_ma: str | None = None
    mo_ta: str | None = None
    loai_giam_gia: str
    gia_tri_giam: Decimal
    dieu_kien_loai: str | None = None
    so_ngay_thue_toi_thieu: int | None = None
    gia_tri_don_toi_thieu: Decimal | None = None
    ngay_bat_dau: date | None = None
    ngay_ket_thuc: date | None = None
    so_luong: int | None = None
    da_su_dung: int | None = None
    trang_thai: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
