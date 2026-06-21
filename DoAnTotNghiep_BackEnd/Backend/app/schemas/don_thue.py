from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.hang_so import TRANG_THAI_DON_HANG
from app.schemas.chung import MoHinhTienTe
from app.schemas.khach_hang import KhachHangPhanHoi
from app.schemas.thiet_bi import ThietBiPhanHoi

NGAY_NHAN_QUA_KHU_ERROR = "Ngày nhận không được nhỏ hơn ngày hiện tại."
NGAY_TRA_KHONG_HOP_LE_ERROR = "Ngày trả phải lớn hơn ngày nhận."

TRANG_THAI_DON_THUE = Literal[
    "Cho thanh toan",
    "Da dat",
    "Da xac nhan",
    "Dang thue",
    "Da thue",
    "Da qua han",
    "Da huy",
]
trang_thai_don_hang = TRANG_THAI_DON_THUE


class MucDonThueTao(BaseModel):
    id_thiet_bi: int
    ngay_nhan: datetime
    ngay_tra: datetime
    so_luong: int = Field(gt=0, examples=[1])

    @model_validator(mode="after")
    def validate_date_range(self) -> "MucDonThueTao":
        if self.ngay_nhan.date() < date.today():
            raise ValueError(NGAY_NHAN_QUA_KHU_ERROR)
        if self.ngay_tra <= self.ngay_nhan:
            raise ValueError(NGAY_TRA_KHONG_HOP_LE_ERROR)
        return self


class DonThueTao(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_khach_hang: int | None = Field(
        default=None,
        validation_alias=AliasChoices("id_khach_hang", "Id_khach_hang"),
    )
    anh_chuyen_khoan: str | None = Field(
        default=None,
        validation_alias=AliasChoices("anh_chuyen_khoan", "Anh_chuyen_khoan"),
    )
    phuong_thuc_thanh_toan: Literal["VNPAY", "Chuyen khoan thu cong"] | None = None
    id_ma_giam_gia: int | None = Field(default=None, validation_alias=AliasChoices("id_ma_giam_gia", "discount_id"))
    ma_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ma_code", "ma_giam_gia", "code", "discountCode"),
        max_length=50,
    )
    ghi_chu: str | None = Field(default=None, max_length=255)
    items: list[MucDonThueTao] = Field(
        min_length=1,
        validation_alias=AliasChoices("danh_sach_thiet_bi", "items"),
        serialization_alias="danh_sach_thiet_bi",
    )

    @field_validator("ma_code")
    @classmethod
    def normalize_discount_code(cls, value: str | None) -> str | None:
        value = value.strip().upper() if isinstance(value, str) else value
        return value or None


class TrangThaiDonThueCapNhat(BaseModel):
    trang_thai: TRANG_THAI_DON_THUE = Field(examples=[TRANG_THAI_DON_HANG[1]])


class HuyDonThueYeuCau(BaseModel):
    ly_do_huy: str | None = Field(default=None, max_length=255)


class HuyDonThuePhanHoi(BaseModel):
    message: str
    Id_don_thue: int
    trang_thai: str | None = None


class ChiTietDonThuePhanHoi(MoHinhTienTe):
    id_chi_tiet_don_thue: int
    id_don_thue: int | None = None
    id_thiet_bi: int | None = None
    ngay_nhan: datetime | None = None
    ngay_tra: datetime | None = None
    so_luong: int | None = None
    gia_thue: Decimal | None = None
    device: ThietBiPhanHoi | None = None


class DonThuePhanHoi(MoHinhTienTe):
    id_don_thue: int
    id_khach_hang: int | None = None
    ngay_dat: datetime | None = None
    trang_thai: str | None = None
    tong_tien: Decimal | None = None
    id_ma_giam_gia: int | None = None
    so_tien_giam: Decimal | None = None
    anh_chuyen_khoan: str | None = None
    phuong_thuc_thanh_toan: str | None = None
    ma_giao_dich_vnpay: str | None = None
    so_tien_da_thanh_toan: Decimal | None = None
    han_thanh_toan_vnpay: datetime | None = None
    ngay_thanh_toan: datetime | None = None
    ghi_chu: str | None = None
    anh_cccd_mat_truoc: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "anh_cccd_mat_truoc",
            AliasPath("customer", "anh_cccd_mat_truoc"),
            AliasPath("khach_hang", "anh_cccd_mat_truoc"),
        ),
    )
    anh_cccd_mat_sau: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "anh_cccd_mat_sau",
            AliasPath("customer", "anh_cccd_mat_sau"),
            AliasPath("khach_hang", "anh_cccd_mat_sau"),
        ),
    )
    khach_hang: KhachHangPhanHoi | None = Field(
        default=None,
        validation_alias=AliasChoices("khach_hang", "customer"),
    )
    details: list[ChiTietDonThuePhanHoi] = []
