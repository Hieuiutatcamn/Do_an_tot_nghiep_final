from datetime import date, datetime, time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.thiet_bi import ThietBi
from app.models.don_thue import DonThue, ChiTietDonThue

TRANG_THAI_DON_THUE_DANG_HOAT_DONG = (
    "Cho thanh toan",
    "Da dat",
    "Da xac nhan",
    "Dang thue",
)
NGAY_NHAN_QUA_KHU_ERROR = "Ngày nhận không được nhỏ hơn ngày hiện tại."
NGAY_TRA_KHONG_HOP_LE_ERROR = "Ngày trả phải lớn hơn ngày nhận."
THONG_BAO_THIET_BI_SAN_SANG = "Có thể thuê"
THONG_BAO_THIET_BI_HET_HANG = "Thiết bị hiện không còn số lượng khả dụng."
THONG_BAO_TRUNG_LICH_THUE = "Thiết bị này đã được đặt trong khoảng thời gian bạn chọn."


def _chuyen_sang_ngay_gio(value: date | datetime, *, end_of_range: bool = False) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min if end_of_range else time.min)


def chuan_hoa_khoang_thue(start: date | datetime, end: date | datetime) -> tuple[datetime, datetime]:
    start_at = _chuyen_sang_ngay_gio(start)
    end_at = _chuyen_sang_ngay_gio(end, end_of_range=True)
    if start_at.date() < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=NGAY_NHAN_QUA_KHU_ERROR,
        )
    if end_at <= start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=NGAY_TRA_KHONG_HOP_LE_ERROR,
        )
    return start_at, end_at


def _thong_bao_kha_nang_cho_thue(total_quantity: int, booked_quantity: int, available_quantity: int, requested_quantity: int) -> str:
    if available_quantity >= requested_quantity:
        return THONG_BAO_THIET_BI_SAN_SANG
    if total_quantity <= 0:
        return THONG_BAO_THIET_BI_HET_HANG
    if booked_quantity > 0:
        return THONG_BAO_TRUNG_LICH_THUE
    return THONG_BAO_THIET_BI_HET_HANG


def tinh_so_luong_da_dat(
    db: Session,
    id_thiet_bi: int,
    start: date | datetime,
    end: date | datetime,
) -> int:
    start_at, end_at = chuan_hoa_khoang_thue(start, end)
    quantity = db.scalar(
        select(func.coalesce(func.sum(ChiTietDonThue.so_luong), 0))
        .join(DonThue, ChiTietDonThue.id_don_thue == DonThue.id_don_thue)
        .where(
            ChiTietDonThue.id_thiet_bi == id_thiet_bi,
            DonThue.trang_thai.in_(TRANG_THAI_DON_THUE_DANG_HOAT_DONG),
            ChiTietDonThue.ngay_nhan < end_at,
            ChiTietDonThue.ngay_tra > start_at,
        )
    )
    return int(quantity or 0)


def tom_tat_kha_dung(
    db: Session,
    id_thiet_bi: int,
    start: date | datetime,
    end: date | datetime,
    requested_quantity: int = 1,
    device: ThietBi | None = None,
) -> dict[str, Any]:
    start_at, end_at = chuan_hoa_khoang_thue(start, end)
    device = device or db.get(ThietBi, id_thiet_bi)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thiết bị")

    total_quantity = int(device.so_luong or 0)
    booked_quantity = tinh_so_luong_da_dat(db, device.id_thiet_bi, start_at, end_at)
    available_quantity = max(0, total_quantity - booked_quantity)
    requested_quantity = max(1, int(requested_quantity or 1))
    return {
        "Id_thiet_bi": device.id_thiet_bi,
        "id_thiet_bi": device.id_thiet_bi,
        "ten_thiet_bi": device.ten_thiet_bi,
        "tong_so_luong": total_quantity,
        "so_luong_da_dat": booked_quantity,
        "so_luong_kha_dung": available_quantity,
        "remaining_quantity": available_quantity,
        "available": available_quantity >= requested_quantity,
        "so_luong": available_quantity,
        "con_hang": available_quantity > 0,
        "message": _thong_bao_kha_nang_cho_thue(total_quantity, booked_quantity, available_quantity, requested_quantity),
        "tinh_trang": device.tinh_trang,
    }


def dam_bao_kha_dung(
    db: Session,
    device: ThietBi,
    start: date | datetime,
    end: date | datetime,
    requested_quantity: int,
    extra_reserved_quantity: int = 0,
) -> dict[str, Any]:
    summary = tom_tat_kha_dung(db, device.id_thiet_bi, start, end, requested_quantity, device=device)
    available_quantity = max(0, int(summary["so_luong_kha_dung"]) - max(0, int(extra_reserved_quantity or 0)))
    if available_quantity < requested_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=summary.get("message") or THONG_BAO_THIET_BI_HET_HANG,
        )
    summary["so_luong_kha_dung"] = available_quantity
    summary["remaining_quantity"] = available_quantity
    summary["so_luong"] = available_quantity
    summary["available"] = True
    summary["con_hang"] = available_quantity > 0
    summary["message"] = THONG_BAO_THIET_BI_SAN_SANG
    return summary
