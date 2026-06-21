from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.thong_bao import (
    CapNhatNhieuThongBaoPhanHoi,
    ThongBaoTao,
    ThongBaoPhanHoi,
    TrangThaiThongBao,
    DemThongBaoChuaDocPhanHoi,
)
from app.services import thong_bao_service
from app.utils.dependencies import get_current_account, require_admin

router = APIRouter(prefix="/thong-bao", tags=["Thông báo"])


@router.get("", response_model=list[ThongBaoPhanHoi])
def lay_danh_sach_thong_bao(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    trang_thai: Annotated[TrangThaiThongBao | None, Query()] = None,
) -> list[ThongBaoPhanHoi]:
    return thong_bao_service.lay_danh_sach_thong_bao(db, account, status_filter=trang_thai)


@router.get("/unread-count", response_model=DemThongBaoChuaDocPhanHoi)
def dem_thong_bao_chua_doc(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> DemThongBaoChuaDocPhanHoi:
    return DemThongBaoChuaDocPhanHoi(dem_thong_bao_chua_doc=thong_bao_service.dem_thong_bao_chua_doc(db, account))


@router.put("/read-all", response_model=CapNhatNhieuThongBaoPhanHoi)
def danh_dau_tat_ca_da_doc(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> CapNhatNhieuThongBaoPhanHoi:
    return CapNhatNhieuThongBaoPhanHoi(updated=thong_bao_service.danh_dau_tat_ca_da_doc(db, account))


@router.put("/{notification_id}/read", response_model=ThongBaoPhanHoi)
def danh_dau_da_doc(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> ThongBaoPhanHoi:
    return thong_bao_service.danh_dau_da_doc(db, notification_id, account)


@router.post("", response_model=ThongBaoPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_thong_bao(
    payload: ThongBaoTao,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
) -> ThongBaoPhanHoi:
    return thong_bao_service.tao_thong_bao(db, payload)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_thong_bao(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> None:
    thong_bao_service.xoa_thong_bao(db, notification_id, account)


legacy_router = tao_router_ke_thua(router, "/notifications", tags=["Thông báo legacy"])
