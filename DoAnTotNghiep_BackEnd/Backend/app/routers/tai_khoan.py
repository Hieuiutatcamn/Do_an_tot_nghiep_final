from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.tai_khoan import TaiKhoanTao, TaiKhoanCapNhatMatKhau, TaiKhoanPhanHoi, TaiKhoanCapNhat
from app.services import tai_khoan_service
from app.utils.dependencies import require_admin
from app.utils.pagination import Page, PaginationParams, build_page

router = APIRouter(prefix="/tai-khoan", tags=["Tài khoản"])


@router.get("", response_model=Page[TaiKhoanPhanHoi])
def lay_danh_sach_tai_khoan(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> Page[TaiKhoanPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = tai_khoan_service.lay_danh_sach_tai_khoan(db, params)
    return build_page(items, total, params)


@router.get("/{account_id}", response_model=TaiKhoanPhanHoi)
def get_account(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return tai_khoan_service._tim_kiem_tai_khoan(db, account_id)


@router.post("", response_model=TaiKhoanPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_tai_khoan(
    payload: TaiKhoanTao,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return tai_khoan_service.tao_tai_khoan(db, payload)


@router.put("/{account_id}", response_model=TaiKhoanPhanHoi)
def cap_nhat_tai_khoan(
    account_id: int,
    payload: TaiKhoanCapNhat,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return tai_khoan_service.cap_nhat_tai_khoan(db, account_id, payload)


@router.patch("/{account_id}/password", response_model=TaiKhoanPhanHoi)
def cap_nhat_mat_khau_tai_khoan(
    account_id: int,
    payload: TaiKhoanCapNhatMatKhau,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return tai_khoan_service.cap_nhat_mat_khau(db, account_id, payload)


@router.delete("/{account_id}", response_model=TaiKhoanPhanHoi)
def vo_hieu_hoa_tai_khoan(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return tai_khoan_service.vo_hieu_hoa_tai_khoan(db, account_id)


legacy_router = tao_router_ke_thua(router, "/accounts", tags=["Tài khoản legacy"])
