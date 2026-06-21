from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.gio_hang import MucGioHangTao, MucGioHangPhanHoi, MucGioHangCapNhat, GioHangPhanHoi
from app.services import gio_hang_service
from app.utils.dependencies import get_current_account

router = APIRouter(prefix="/gio-hang", tags=["Giỏ hàng"])


@router.get("", response_model=GioHangPhanHoi)
def lay_gio_hang(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> GioHangPhanHoi:
    return gio_hang_service.lay_gio_hang(db, account)


@router.post("", response_model=MucGioHangPhanHoi, status_code=status.HTTP_201_CREATED)
def them_vao_gio_hang(
    payload: MucGioHangTao,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> MucGioHangPhanHoi:
    return gio_hang_service.them_vao_gio_hang(db, payload, account)


@router.put("/{cart_item_id}", response_model=MucGioHangPhanHoi)
def cap_nhat_muc_gio_hang(
    cart_item_id: int,
    payload: MucGioHangCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> MucGioHangPhanHoi:
    return gio_hang_service.cap_nhat_muc_gio_hang(db, cart_item_id, payload, account)


@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_muc_gio_hang(
    cart_item_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> None:
    gio_hang_service.xoa_muc_gio_hang(db, cart_item_id, account)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def xoa_gio_hang(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> None:
    gio_hang_service.xoa_gio_hang(db, account)


legacy_router = tao_router_ke_thua(router, "/cart", tags=["Giỏ hàng legacy"])
