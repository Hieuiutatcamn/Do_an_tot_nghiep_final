from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import TAI_KHOAN_HOAT_DONG, VAI_TRO_KHACH_HANG
from app.models.khach_hang import KhachHang
from app.schemas.xac_thuc import DangNhapYeuCau, DangKyYeuCau, DoiMatKhauYeuCau, TokenPhanHoi
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)


def kiem_tra_dang_ky_khong_trung(db: Session, payload: DangKyYeuCau) -> None:
    errors: list[str] = []
    cccd = payload.so_cccd or payload.cccd
    email = str(payload.email) if payload.email else None

    if db.scalar(select(TaiKhoan).where(TaiKhoan.dang_nhap == payload.username)):
        errors.append("Tên đăng nhập đã tồn tại")
    if payload.sdt and db.scalar(select(KhachHang).where(KhachHang.sdt == payload.sdt)):
        errors.append("Số điện thoại đã được sử dụng")
    if cccd and db.scalar(select(KhachHang).where(KhachHang.so_cccd == cccd)):
        errors.append("Số CCCD đã được sử dụng")
    if email and db.scalar(select(KhachHang).where(KhachHang.email == email)):
        errors.append("Email đã được sử dụng")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0] if len(errors) == 1 else errors,
        )


def dang_ky_khach_hang(db: Session, payload: DangKyYeuCau) -> TokenPhanHoi:
    kiem_tra_dang_ky_khong_trung(db, payload)

    account = TaiKhoan(
        dang_nhap=payload.username,
        mat_khau=hash_password(payload.password),
        vai_tro=VAI_TRO_KHACH_HANG,
        trang_thai=TAI_KHOAN_HOAT_DONG,
        key=True,
    )
    db.add(account)
    db.flush()

    customer = KhachHang(
        id_tai_khoan=account.id_tai_khoan,
        ho_ten=payload.ho_ten,
        sdt=payload.sdt,
        so_cccd=payload.so_cccd or payload.cccd,
        email=str(payload.email) if payload.email else None,
        anh_cccd_mat_truoc=payload.anh_cccd_mat_truoc,
        anh_cccd_mat_sau=payload.anh_cccd_mat_sau,
        anh_cccd=payload.anh_cccd,
    )
    db.add(customer)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        kiem_tra_dang_ky_khong_trung(db, payload)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thông tin đăng ký đã tồn tại",
        ) from exc
    db.refresh(account)

    return tao_phan_hoi_token(account.id_tai_khoan)


def _lay_thong_bao_co_quyen_truy_cap(db: Session, payload: DangNhapYeuCau) -> TokenPhanHoi:
    account = db.scalar(select(TaiKhoan).where(TaiKhoan.dang_nhap == payload.username))
    if not account or not verify_password(payload.password, account.mat_khau):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if account.trang_thai and account.trang_thai != TAI_KHOAN_HOAT_DONG:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đang bị khóa")

    if password_needs_rehash(account.mat_khau):
        account.mat_khau = hash_password(payload.password)
        db.add(account)
        db.commit()

    return tao_phan_hoi_token(account.id_tai_khoan)


def doi_mat_khau(db: Session, account: TaiKhoan, payload: DoiMatKhauYeuCau) -> None:
    if not verify_password(payload.mat_khau_hien_tai, account.mat_khau):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không đúng",
        )
    if verify_password(payload.mat_khau_moi, account.mat_khau):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới không được trùng mật khẩu hiện tại",
        )

    account.mat_khau = hash_password(payload.mat_khau_moi)
    db.add(account)
    db.commit()


def tao_phan_hoi_token(account_id: int) -> TokenPhanHoi:
    subject = str(account_id)
    return TokenPhanHoi(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )
