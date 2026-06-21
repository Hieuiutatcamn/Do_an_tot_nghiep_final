from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.don_thue import (
    HuyDonThueYeuCau,
    HuyDonThuePhanHoi,
    DonThueTao,
    DonThuePhanHoi,
    TRANG_THAI_DON_THUE,
    TrangThaiDonThueCapNhat,
)
from app.services import don_thue_service
from app.utils.dependencies import get_current_account
from app.utils.pagination import Page, PaginationParams, build_page
from app.utils.upload import delete_upload_file, save_upload_file

router = APIRouter(prefix="/rentals", tags=["Đơn thuê"])


@router.post("", response_model=DonThuePhanHoi, status_code=status.HTTP_201_CREATED)
def tao_don_thue_endpoint(
    payload: DonThueTao,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return don_thue_service.tao_don_thue(db, payload, account)


@router.get("", response_model=Page[DonThuePhanHoi])
def lay_danh_sach_don_thue(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
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


@router.get("/me/history", response_model=Page[DonThuePhanHoi])
def lich_su_don_thue_cua_toi(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> Page[DonThuePhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = don_thue_service.lay_danh_sach_don_thue(db, params, account)
    return build_page(items, total, params)


@router.get("/{rental_id}", response_model=DonThuePhanHoi)
def lay_don_thue(
    rental_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return don_thue_service.tim_kiem_don_thue(db, rental_id, account)


@router.patch("/{rental_id}/status", response_model=DonThuePhanHoi)
def cap_nhat_trang_thai_don_thue(
    rental_id: int,
    payload: TrangThaiDonThueCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return don_thue_service.cap_nhat_trang_thai_don_thue(db, rental_id, payload, account)


@router.patch("/{rental_id}/cancel", response_model=HuyDonThuePhanHoi)
def huy_don_thue_endpoint(
    rental_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    payload: Annotated[HuyDonThueYeuCau | None, Body()] = None,
):
    rental = don_thue_service.huy_don_thue(
        db,
        rental_id,
        account,
        reason=payload.ly_do_huy if payload else None,
    )
    return HuyDonThuePhanHoi(
        message="Hủy đơn hàng thành công",
        Id_don_thue=rental.id_don_thue,
        trang_thai=rental.trang_thai,
    )


@router.put("/{rental_id}/payment-image", response_model=DonThuePhanHoi)
async def cap_nhat_anh_thanh_toan_don_thue(
    rental_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    anh_chuyen_khoan: Annotated[UploadFile, File(...)],
):
    rental = don_thue_service.lay_don_thue_cho_cap_nhat_nguoi_dung(db, rental_id, account)
    old_image_path = rental.anh_chuyen_khoan
    image_path = await save_upload_file(anh_chuyen_khoan, "payment")
    try:
        updated_rental = don_thue_service.cap_nhat_anh_thanh_toan_don_thue(
            db,
            rental_id,
            image_path,
            account,
        )
    except Exception:
        delete_upload_file(image_path)
        raise

    if old_image_path and old_image_path != image_path:
        delete_upload_file(old_image_path)
    return updated_rental


@router.put("/{rental_id}/khach_hang_update", response_model=DonThuePhanHoi)
async def cap_nhat_thong_tin_don_thue_nguoi_dung(
    rental_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    ho_ten: Annotated[str, Form(...)],
    sdt: Annotated[str, Form(...)],
    dia_chi: Annotated[str, Form(...)],
    ghi_chu: Annotated[str | None, Form()] = None,
    anh_chuyen_khoan: Annotated[UploadFile | None, File()] = None,
    Anh_chuyen_khoan: Annotated[UploadFile | None, File()] = None,
):
    rental = don_thue_service.lay_don_thue_cho_cap_nhat_nguoi_dung(db, rental_id, account)
    old_image_path = rental.anh_chuyen_khoan
    upload_file = anh_chuyen_khoan or Anh_chuyen_khoan
    image_path = await save_upload_file(upload_file, "payment") if upload_file else None

    try:
        updated_rental = don_thue_service.cap_nhat_thong_tin_don_thue_nguoi_dung(
            db,
            rental_id,
            account,
            ho_ten=ho_ten,
            sdt=sdt,
            dia_chi=dia_chi,
            ghi_chu=ghi_chu,
            image_path=image_path,
        )
    except Exception:
        if image_path:
            delete_upload_file(image_path)
        raise

    if image_path and old_image_path and old_image_path != image_path:
        delete_upload_file(old_image_path)
    return updated_rental


legacy_router = tao_router_ke_thua(router, "/don-thue", tags=["Đơn thuê legacy"])
