from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import VAI_TRO_KHACH_HANG
from app.models.khach_hang import KhachHang
from app.schemas.khach_hang import KhachHangTao, KhachHangCapNhat
from app.utils.pagination import PaginationParams


def lay_danh_sach_khach_hang(db: Session, params: PaginationParams) -> tuple[list[KhachHang], int]:
    total = db.scalar(select(func.count()).select_from(KhachHang)) or 0
    customers = db.scalars(
        select(KhachHang)
        .options(selectinload(KhachHang.account))
        .order_by(KhachHang.id_khach_hang.asc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(customers), total


def tim_kiem_khach_hang(db: Session, customer_id: int) -> KhachHang:
    customer = db.scalar(
        select(KhachHang)
        .options(selectinload(KhachHang.account))
        .where(KhachHang.id_khach_hang == customer_id)
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy khách hàng.")
    return customer


def _kiem_tra_lien_ket_tai_khoan(
    db: Session,
    account_id: int | None,
    ignore_customer_id: int | None = None,
) -> None:
    if account_id is None:
        return
    account = db.get(TaiKhoan, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không tìm thấy tài khoản.")
    if account.vai_tro and account.vai_tro != VAI_TRO_KHACH_HANG:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vai trò của tài khoản phải là Khách hàng.")

    stmt = select(KhachHang).where(KhachHang.id_tai_khoan == account_id)
    if ignore_customer_id is not None:
        stmt = stmt.where(KhachHang.id_khach_hang != ignore_customer_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tài khoản đã được liên kết với một khách hàng khác.")


def tao_khach_hang(db: Session, payload: KhachHangTao) -> KhachHang:
    _kiem_tra_lien_ket_tai_khoan(db, payload.id_tai_khoan)
    customer = KhachHang(**_chuan_hoa_du_lieu_khach_hang(payload.model_dump()))
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return tim_kiem_khach_hang(db, customer.id_khach_hang)


def _chuan_hoa_du_lieu_khach_hang(data: dict) -> dict:
    normalized = dict(data)
    if "cccd" in normalized:
        cccd = normalized.pop("cccd")
        if "so_cccd" not in normalized or normalized.get("so_cccd") in (None, ""):
            normalized["so_cccd"] = cccd
    return normalized


def cap_nhat_khach_hang(db: Session, customer_id: int, payload: KhachHangCapNhat) -> KhachHang:
    customer = tim_kiem_khach_hang(db, customer_id)
    data = _chuan_hoa_du_lieu_khach_hang(payload.model_dump(exclude_unset=True))
    if "id_tai_khoan" in data:
        _kiem_tra_lien_ket_tai_khoan(db, data["id_tai_khoan"], ignore_customer_id=customer_id)
    for field, value in data.items():
        setattr(customer, field, value)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return tim_kiem_khach_hang(db, customer.id_khach_hang)


def xoa_khach_hang(db: Session, customer_id: int) -> None:
    customer = tim_kiem_khach_hang(db, customer_id)
    db.delete(customer)
    db.commit()
