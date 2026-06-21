from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.gio_hang import GioHang
from app.models.thiet_bi import ThietBi
from app.schemas.gio_hang import MucGioHangTao, MucGioHangPhanHoi, MucGioHangCapNhat, GioHangPhanHoi
from app.services import kiem_tra_lich_thue_service

NGAY_NHAN_QUA_KHU_ERROR = "Ngày nhận không được nhỏ hơn ngày hiện tại."
NGAY_TRA_KHONG_HOP_LE_ERROR = "Ngày trả phải lớn hơn ngày nhận."


def _require_customer_id(account: TaiKhoan) -> int:
    if not account.customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=" Không tìm thấy thông tin khách hàng.")
    return account.customer.id_khach_hang


def _ngay_thue(start: date | None, end: date | None) -> int:
    if not start or not end:
        return 0
    return max(0, (end - start).days)


def _money_to_int(value: Decimal | int | float | None) -> int:
    return int(value or 0)


def _chi_tiet_gio_hang_response(item: GioHang) -> MucGioHangPhanHoi:
    device = item.device
    days = _ngay_thue(item.ngay_nhan, item.ngay_tra)
    quantity = item.so_luong or 0
    unit_price = _money_to_int(device.gia_thue if device else 0)
    return MucGioHangPhanHoi(
        id_gio_hang=item.id_gio_hang,
        id_thiet_bi=item.id_thiet_bi,
        ten_thiet_bi=device.ten_thiet_bi if device else None,
        hinh_anh=device.hinh_anh if device else None,
        trang_thai=device.tinh_trang if device else None,
        ngay_nhan=item.ngay_nhan,
        ngay_tra=item.ngay_tra,
        so_ngay_thue=days,
        gia_thue=unit_price,
        so_luong=quantity,
        thanh_tien=days * unit_price * quantity,
    )


def _get_gio_hang_dang_co(db: Session, cart_item_id: int, customer_id: int) -> GioHang:
    item = db.scalar(
        select(GioHang)
        .options(selectinload(GioHang.device))
        .where(
            GioHang.id_gio_hang == cart_item_id,
            GioHang.id_khach_hang == customer_id,
        )
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    return item


def _kiem_tra_ngay_nhan_va_ngay_tra(start: date | None, end: date | None) -> None:
    if not start or not end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày nhận và ngày trả là bắt buộc.",
        )
    if start < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=NGAY_NHAN_QUA_KHU_ERROR,
        )
    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=NGAY_TRA_KHONG_HOP_LE_ERROR,
        )


def lay_gio_hang(db: Session, account: TaiKhoan) -> GioHangPhanHoi:
    customer_id = _require_customer_id(account)
    items = db.scalars(
        select(GioHang)
        .options(selectinload(GioHang.device))
        .where(GioHang.id_khach_hang == customer_id)
        .order_by(GioHang.ngay_them.desc(), GioHang.id_gio_hang.desc())
    ).all()
    response_items = [_chi_tiet_gio_hang_response(item) for item in items]
    return GioHangPhanHoi(
        items=response_items,
        tong_san_pham=sum(item.so_luong for item in response_items),
        tong_so_ngay_thue=sum(item.so_ngay_thue for item in response_items),
        tong_tien_thue=sum(item.thanh_tien for item in response_items),
    )


def them_vao_gio_hang(db: Session, payload: MucGioHangTao, account: TaiKhoan) -> MucGioHangPhanHoi:
    customer_id = _require_customer_id(account)
    device = db.get(ThietBi, payload.id_thiet_bi)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ThietBi not found")
    _kiem_tra_ngay_nhan_va_ngay_tra(payload.ngay_nhan, payload.ngay_tra)
    kiem_tra_lich_thue_service.dam_bao_kha_dung(
        db,
        device,
        payload.ngay_nhan,
        payload.ngay_tra,
        payload.so_luong,
    )

    existing_item = db.scalar(
        select(GioHang)
        .where(
            GioHang.id_khach_hang == customer_id,
            GioHang.id_thiet_bi == payload.id_thiet_bi,
        )
        .limit(1)
    )
    if existing_item:
        existing_item.so_luong = payload.so_luong
        existing_item.ngay_nhan = payload.ngay_nhan
        existing_item.ngay_tra = payload.ngay_tra
        db.add(existing_item)
        db.commit()
        return _chi_tiet_gio_hang_response(_get_gio_hang_dang_co(db, existing_item.id_gio_hang, customer_id))

    item = GioHang(
        id_khach_hang=customer_id,
        id_thiet_bi=payload.id_thiet_bi,
        so_luong=payload.so_luong,
        ngay_nhan=payload.ngay_nhan,
        ngay_tra=payload.ngay_tra,
    )
    db.add(item)
    db.commit()
    return _chi_tiet_gio_hang_response(_get_gio_hang_dang_co(db, item.id_gio_hang, customer_id))


def cap_nhat_muc_gio_hang(
    db: Session,
    cart_item_id: int,
    payload: MucGioHangCapNhat,
    account: TaiKhoan,
) -> MucGioHangPhanHoi:
    customer_id = _require_customer_id(account)
    item = _get_gio_hang_dang_co(db, cart_item_id, customer_id)
    data = payload.model_dump(exclude_unset=True)

    if "so_luong" in data:
        item.so_luong = data["so_luong"]
    if "ngay_nhan" in data:
        item.ngay_nhan = data["ngay_nhan"]
    if "ngay_tra" in data:
        item.ngay_tra = data["ngay_tra"]

    _kiem_tra_ngay_nhan_va_ngay_tra(item.ngay_nhan, item.ngay_tra)
    if not item.device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ThietBi not found")
    kiem_tra_lich_thue_service.dam_bao_kha_dung(
        db,
        item.device,
        item.ngay_nhan,
        item.ngay_tra,
        item.so_luong or 1,
    )
    db.add(item)
    db.commit()
    return _chi_tiet_gio_hang_response(_get_gio_hang_dang_co(db, item.id_gio_hang, customer_id))


def xoa_muc_gio_hang(db: Session, cart_item_id: int, account: TaiKhoan) -> None:
    customer_id = _require_customer_id(account)
    item = _get_gio_hang_dang_co(db, cart_item_id, customer_id)
    db.delete(item)
    db.commit()


def xoa_gio_hang(db: Session, account: TaiKhoan) -> None:
    xoa_gio_hang_theo_khach_hang(db, _require_customer_id(account))


def xoa_gio_hang_theo_khach_hang(db: Session, customer_id: int, commit: bool = True) -> int:
    result = db.execute(delete(GioHang).where(GioHang.id_khach_hang == customer_id))
    if commit:
        db.commit()
    return result.rowcount or 0


def _date_value(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def gio_hang_khop_muc_don_thue(db: Session, customer_id: int, rental_items: list[Any]) -> bool:
    cart_items = db.scalars(select(GioHang).where(GioHang.id_khach_hang == customer_id)).all()
    if not cart_items or len(cart_items) != len(rental_items):
        return False

    cart_map = {
        item.id_thiet_bi: (
            item.so_luong,
            item.ngay_nhan,
            item.ngay_tra,
        )
        for item in cart_items
    }
    rental_map = {
        item.id_thiet_bi: (
            item.so_luong,
            _date_value(item.ngay_nhan),
            _date_value(item.ngay_tra),
        )
        for item in rental_items
    }
    return cart_map == rental_map
