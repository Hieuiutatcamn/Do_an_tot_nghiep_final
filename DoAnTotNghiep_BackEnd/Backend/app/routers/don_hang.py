from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.tai_khoan import TaiKhoan
from app.routers.router_ke_thua import tao_router_ke_thua
from app.schemas.don_thue import (
    HuyDonThueYeuCau,
    HuyDonThuePhanHoi,
    ChiTietDonThuePhanHoi,
    DonThuePhanHoi,
    TRANG_THAI_DON_THUE,
)
from app.services import don_thue_service
from app.utils.dependencies import get_current_account
from app.utils.pagination import Page, PaginationParams, build_page
from app.utils.upload import delete_upload_file, save_upload_file

router = APIRouter(prefix="/don-hang", tags=["Đơn hàng"])
chi_tiet_don_hang_router = APIRouter(prefix="/chi-tiet-don-hang", tags=["Chi tiết đơn hàng"])


@router.get("", response_model=Page[DonThuePhanHoi])
def lay_danh_sach_don_hang(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
    trang_thai: TRANG_THAI_DON_THUE | None = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
) -> Page[DonThuePhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = don_thue_service.lay_danh_sach_don_thue(
        db,
        params,
        account,
        status_filter=trang_thai,
        search=search,
    )
    return build_page(items, total, params)


@router.get("/my-orders", response_model=Page[DonThuePhanHoi])
def lay_don_hang_cua_toi(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
    search: Annotated[str | None, Query(max_length=255)] = None,
) -> Page[DonThuePhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = don_thue_service.lay_danh_sach_don_thue(db, params, account, search=search)
    return build_page(items, total, params)


@router.get("/{order_id}", response_model=DonThuePhanHoi)
def lay_don_hang(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return don_thue_service.tim_kiem_don_thue(db, order_id, account)


@router.patch("/{order_id}/cancel", response_model=HuyDonThuePhanHoi)
def huy_don_hang(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    payload: Annotated[HuyDonThueYeuCau | None, Body()] = None,
):
    rental = don_thue_service.huy_don_thue(
        db,
        order_id,
        account,
        reason=payload.ly_do_huy if payload else None,
    )
    return HuyDonThuePhanHoi(
        message="Hủy đơn hàng thành công",
        Id_don_thue=rental.id_don_thue,
        trang_thai=rental.trang_thai,
    )


@router.put("/{order_id}/payment-image", response_model=DonThuePhanHoi)
async def cap_nhat_anh_thanh_toan_don_hang(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    anh_chuyen_khoan: Annotated[UploadFile, File(...)],
):
    rental = don_thue_service.lay_don_thue_cho_cap_nhat_nguoi_dung(db, order_id, account)
    old_image_path = rental.anh_chuyen_khoan
    image_path = await save_upload_file(anh_chuyen_khoan, "payment")
    try:
        updated_rental = don_thue_service.cap_nhat_anh_thanh_toan_don_thue(
            db,
            order_id,
            image_path,
            account,
        )
    except Exception:
        delete_upload_file(image_path)
        raise

    if old_image_path and old_image_path != image_path:
        delete_upload_file(old_image_path)
    return updated_rental


@chi_tiet_don_hang_router.get("", response_model=list[ChiTietDonThuePhanHoi])
def lay_chi_tiet_don_hang(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    order = don_thue_service.tim_kiem_don_thue(db, order_id, account)
    return list(order.details)


legacy_router = tao_router_ke_thua(router, "/orders", tags=["Đơn hàng legacy"])
legacy_chi_tiet_don_hang_router = tao_router_ke_thua(
    chi_tiet_don_hang_router,
    "/order-details",
    tags=["Chi tiết đơn hàng legacy"],
)
