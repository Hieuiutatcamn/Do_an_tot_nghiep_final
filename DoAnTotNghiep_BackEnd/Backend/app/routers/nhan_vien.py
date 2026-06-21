from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.nhan_vien import NhanVienTao, NhanVienPhanHoi, NhanVienCapNhat
from app.services import nhan_vien_service
from app.utils.dependencies import require_admin
from app.utils.pagination import Page, PaginationParams, build_page

router = APIRouter(prefix="/nhan-vien", tags=["Nhân viên"])


@router.get("", response_model=Page[NhanVienPhanHoi])
def lay_danh_sach_nhan_vien(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> Page[NhanVienPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = nhan_vien_service.lay_danh_sach_nhan_vien(db, params)
    return build_page(items, total, params)


@router.get("/{employee_id}", response_model=NhanVienPhanHoi)
def lay_nhan_vien(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return nhan_vien_service.lay_nhan_vien_hoac_404(db, employee_id)


@router.post("", response_model=NhanVienPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_nhan_vien(
    payload: NhanVienTao,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return nhan_vien_service.tao_nhan_vien(db, payload)


@router.put("/{employee_id}", response_model=NhanVienPhanHoi)
def cap_nhat_nhan_vien(
    employee_id: int,
    payload: NhanVienCapNhat,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return nhan_vien_service.cap_nhat_nhan_vien(db, employee_id, payload)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_nhan_vien(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
) -> None:
    nhan_vien_service.xoa_nhan_vien(db, employee_id)


legacy_router = tao_router_ke_thua(router, "/employees", tags=["Nhân viên legacy"])
