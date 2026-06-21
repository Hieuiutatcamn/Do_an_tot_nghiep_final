from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.danh_muc import DanhMucTao, DanhMucPhanHoi, DanhMucCapNhat
from app.services import danh_muc_service
from app.utils.dependencies import require_admin
from app.utils.pagination import Page, PaginationParams, build_page

router = APIRouter(prefix="/danh-muc", tags=["Danh mục"])


@router.get("", response_model=Page[DanhMucPhanHoi])
def lay_danh_sach_danh_muc(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> Page[DanhMucPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = danh_muc_service.lay_danh_sach_danh_muc(db, params)
    return build_page(items, total, params)


@router.get("/{category_id}", response_model=DanhMucPhanHoi)
def lay_danh_muc(category_id: int, db: Annotated[Session, Depends(get_db)]):
    return danh_muc_service.lay_danh_muc_hoac_404(db, category_id)


@router.post("", response_model=DanhMucPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_danh_muc(
    payload: DanhMucTao,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return danh_muc_service.tao_danh_muc(db, payload)


@router.put("/{category_id}", response_model=DanhMucPhanHoi)
def cap_nhat_danh_muc(
    category_id: int,
    payload: DanhMucCapNhat,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return danh_muc_service.cap_nhat_danh_muc(db, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_danh_muc(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
) -> None:
    danh_muc_service.xoa_danh_muc(db, category_id)


legacy_router = tao_router_ke_thua(router, "/categories", tags=["Danh mục legacy"])
