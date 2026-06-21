from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.hang_so import VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN
from app.models.tai_khoan import TaiKhoan
from app.models.khach_hang import KhachHang
from app.utils.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_account(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> TaiKhoan:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, "access")
        account_id = int(payload.get("sub", "0"))
    except (ValueError, TypeError):
        raise credentials_exception

    account = db.get(TaiKhoan, account_id)
    if not account:
        raise credentials_exception
    if account.trang_thai and account.trang_thai != "Hoat dong":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="TaiKhoan is inactive")
    return account


def get_current_customer(
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> KhachHang:
    if not account.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KhachHang profile is required",
        )
    return account.customer


def require_staff(account: Annotated[TaiKhoan, Depends(get_current_account)]) -> TaiKhoan:
    if account.vai_tro not in {VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role is required")
    return account


def require_admin_or_staff(account: Annotated[TaiKhoan, Depends(get_current_account)]) -> TaiKhoan:
    if account.vai_tro not in {VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này.",
        )
    return account


def require_admin(account: Annotated[TaiKhoan, Depends(get_current_account)]) -> TaiKhoan:
    if account.vai_tro != VAI_TRO_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này.",
        )
    return account
