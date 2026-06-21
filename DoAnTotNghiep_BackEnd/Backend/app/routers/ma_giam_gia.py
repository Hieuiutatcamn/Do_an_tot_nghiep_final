from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.ma_giam_gia import (
    ApDungMaGiamGiaYeuCau,
    ApDungMaGiamGiaPhanHoi,
    MaGiamGiaTao,
    MaGiamGiaPhanHoi,
    TrangThaiMaGiamGiaCapNhat,
    MaGiamGiaCapNhat,
)
from app.services import ma_giam_gia_service
from app.utils.dependencies import require_admin, require_admin_or_staff
from app.utils.pagination import Page, PaginationParams, build_page

router = APIRouter(prefix="/ma-giam-gia", tags=["Mã giảm giá"])
admin_router = APIRouter(prefix="/admin/ma-giam-gia", tags=["Admin mã giảm giá"])


@router.get("/active", response_model=list[MaGiamGiaPhanHoi])
def lay_ma_giam_gia_dang_hoat_dong(
    db: Annotated[Session, Depends(get_db)],
) -> list[MaGiamGiaPhanHoi]:
    return ma_giam_gia_service.lay_ma_giam_gia_dang_hoat_dong(db)


@router.post("/apply", response_model=ApDungMaGiamGiaPhanHoi)
def ap_dung_ma_giam_gia(
    payload: ApDungMaGiamGiaYeuCau,
    db: Annotated[Session, Depends(get_db)],
) -> ApDungMaGiamGiaPhanHoi:
    return ma_giam_gia_service.ap_dung_ma_giam_gia(db, payload)


@admin_router.get("", response_model=Page[MaGiamGiaPhanHoi])
def lay_danh_sach_ma_giam_gia_admin(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_admin_or_staff)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(max_length=255)] = None,
    trang_thai: str | None = None,
    loai_giam_gia: str | None = None,
) -> Page[MaGiamGiaPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = ma_giam_gia_service.lay_danh_sach_ma_giam_gia_admin(
        db,
        params,
        account,
        search=search,
        trang_thai=trang_thai,
        loai_giam_gia=loai_giam_gia,
    )
    return build_page(items, total, params)


@admin_router.post("", response_model=MaGiamGiaPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_ma_giam_gia(
    payload: MaGiamGiaTao,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_admin)],
) -> MaGiamGiaPhanHoi:
    return ma_giam_gia_service.tao_ma_giam_gia(db, payload, account)


@admin_router.put("/{discount_id}", response_model=MaGiamGiaPhanHoi)
def cap_nhat_ma_giam_gia(
    discount_id: int,
    payload: MaGiamGiaCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_admin)],
) -> MaGiamGiaPhanHoi:
    return ma_giam_gia_service.cap_nhat_ma_giam_gia(db, discount_id, payload, account)


@admin_router.delete("/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_ma_giam_gia(
    discount_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_admin)],
) -> None:
    ma_giam_gia_service.xoa_ma_giam_gia(db, discount_id, account)


@admin_router.patch("/{discount_id}/status", response_model=MaGiamGiaPhanHoi)
def cap_nhat_trang_thai_ma_giam_gia(
    discount_id: int,
    payload: TrangThaiMaGiamGiaCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_admin)],
) -> MaGiamGiaPhanHoi:
    return ma_giam_gia_service.cap_nhat_trang_thai_ma_giam_gia(db, discount_id, payload, account)


legacy_admin_router = tao_router_ke_thua(
    admin_router,
    "/admin/discounts",
    tags=["Admin mã giảm giá legacy"],
)


legacy_router = tao_router_ke_thua(router, "/discounts", tags=["Mã giảm giá legacy"])
