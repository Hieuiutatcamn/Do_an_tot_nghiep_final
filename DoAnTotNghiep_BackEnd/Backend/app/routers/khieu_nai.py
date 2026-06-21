from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.khieu_nai import (
    KhieuNaiAdminPhanHoi,
    KhieuNaiTao,
    KhieuNaiTaoPhanHoi,
    KhieuNaiPhanHoi,
    TrangThaiKhieuNaiCapNhat,
    KhieuNaiCapNhat,
    KhieuNaiCuaToiPhanHoi,
)
from app.services import khieu_nai_service
from app.utils.dependencies import get_current_account
from app.utils.pagination import Page, PaginationParams, build_page

router = APIRouter(prefix="/khieu-nai", tags=["Khiếu nại"])
admin_router = APIRouter(prefix="/admin/khieu-nai", tags=["Admin khiếu nại"])


@router.get("", response_model=Page[KhieuNaiPhanHoi])
def lay_danh_sach_khieu_nai(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    trang_thai: str | None = None,
) -> Page[KhieuNaiPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = khieu_nai_service.lay_danh_sach_khieu_nai(db, params, account, status_filter=trang_thai)
    return build_page(items, total, params)


@router.get("/my-complaints", response_model=KhieuNaiCuaToiPhanHoi)
def lay_khieu_nai_cua_toi(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> KhieuNaiCuaToiPhanHoi:
    items = khieu_nai_service.lay_khieu_nai_cua_toi(db, account)
    return KhieuNaiCuaToiPhanHoi(items=items)


@router.get("/{complaint_id}", response_model=KhieuNaiPhanHoi)
def lay_khieu_nai(
    complaint_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return khieu_nai_service.lay_khieu_nai_hoac_404(db, complaint_id, account)


@router.post("", response_model=KhieuNaiTaoPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_khieu_nai(
    payload: KhieuNaiTao,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    complaint = khieu_nai_service.tao_khieu_nai(db, payload, account)
    return KhieuNaiTaoPhanHoi(
        message="Gửi khiếu nại thành công",
        id_khieu_nai=complaint.id_khieu_nai,
        trang_thai=complaint.trang_thai,
        tieu_de=complaint.tieu_de,
        noi_dung=complaint.noi_dung,
    )


@router.put("/{complaint_id}", response_model=KhieuNaiPhanHoi)
def cap_nhat_khieu_nai(
    complaint_id: int,
    payload: KhieuNaiCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return khieu_nai_service.cap_nhat_khieu_nai(db, complaint_id, payload, account)


@router.patch("/{complaint_id}/status", response_model=KhieuNaiPhanHoi)
def cap_nhat_trang_thai_khieu_nai(
    complaint_id: int,
    payload: TrangThaiKhieuNaiCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return khieu_nai_service.cap_nhat_trang_thai_khieu_nai(db, complaint_id, payload, account)


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_khieu_nai(
    complaint_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> None:
    khieu_nai_service.xoa_khieu_nai(db, complaint_id, account)


@admin_router.get("", response_model=Page[KhieuNaiAdminPhanHoi])
def lay_danh_sach_khieu_nai_admin(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 100,
) -> Page[KhieuNaiAdminPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = khieu_nai_service.lay_danh_sach_khieu_nai_admin(db, params, account)
    return build_page(items, total, params)


@admin_router.put("/{complaint_id}/status", response_model=KhieuNaiPhanHoi)
def cap_nhat_trang_thai_khieu_nai_admin(
    complaint_id: int,
    payload: TrangThaiKhieuNaiCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    return khieu_nai_service.cap_nhat_trang_thai_khieu_nai(db, complaint_id, payload, account)


legacy_admin_router = tao_router_ke_thua(
    admin_router,
    "/admin/complaints",
    tags=["Admin khiếu nại legacy"],
)


legacy_router = tao_router_ke_thua(router, "/complaints", tags=["Khiếu nại legacy"])
