from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tai_khoan import TaiKhoan
from app.schemas.tai_khoan import TaiKhoanTao, TaiKhoanCapNhatMatKhau, TaiKhoanCapNhat
from app.utils.pagination import PaginationParams
from app.utils.security import hash_password


def lay_danh_sach_tai_khoan(db: Session, params: PaginationParams) -> tuple[list[TaiKhoan], int]:
    total = db.scalar(select(func.count()).select_from(TaiKhoan)) or 0
    accounts = db.scalars(
        select(TaiKhoan)
        .order_by(TaiKhoan.id_tai_khoan.asc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(accounts), total


def _tim_kiem_tai_khoan(db: Session, account_id: int) -> TaiKhoan:
    account = db.get(TaiKhoan, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài khoản")
    return account


def _kiem_tra_ten_dang_nhap_duy_nhat(db: Session, username: str, ignore_account_id: int | None = None) -> None:
    stmt = select(TaiKhoan).where(TaiKhoan.dang_nhap == username)
    if ignore_account_id is not None:
        stmt = stmt.where(TaiKhoan.id_tai_khoan != ignore_account_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã tồn tại")


def tao_tai_khoan(db: Session, payload: TaiKhoanTao) -> TaiKhoan:
    _kiem_tra_ten_dang_nhap_duy_nhat(db, payload.dang_nhap)
    data = payload.model_dump()
    password = data.pop("mat_khau")
    data["mat_khau"] = hash_password(password)
    data["trang_thai"] = data.get("trang_thai") or "Hoat dong"
    data["key"] = True if data.get("key") is None else data.get("key")
    account = TaiKhoan(**data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def cap_nhat_tai_khoan(db: Session, account_id: int, payload: TaiKhoanCapNhat) -> TaiKhoan:
    account = _tim_kiem_tai_khoan(db, account_id)
    data = payload.model_dump(exclude_unset=True)
    if "dang_nhap" in data and data["dang_nhap"]:
        _kiem_tra_ten_dang_nhap_duy_nhat(db, data["dang_nhap"], ignore_account_id=account_id)
    for field, value in data.items():
        setattr(account, field, value)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def cap_nhat_mat_khau(db: Session, account_id: int, payload: TaiKhoanCapNhatMatKhau) -> TaiKhoan:
    account = _tim_kiem_tai_khoan(db, account_id)
    account.mat_khau = hash_password(payload.mat_khau)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def vo_hieu_hoa_tai_khoan(db: Session, account_id: int) -> TaiKhoan:
    account = _tim_kiem_tai_khoan(db, account_id)
    account.trang_thai = "Ngung hoat dong"
    account.key = False
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
