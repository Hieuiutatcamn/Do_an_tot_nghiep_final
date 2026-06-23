from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.models.khach_hang import KhachHang
from app.schemas.tro_chuyen import (
    DanhSachCuocTroChuyenAdminPhanHoi,
    AdminTraLoiNhanVienYeuCau,
    TinNhanTroChuyenPhanHoi,
    GuiTroChuyenYeuCau,
    GuiTroChuyenPhanHoi,
    NhanVienChatYeuCau,
    CuocTroChuyenPhanHoi,
    TicketChatAdminPhanHoi,
    TinNhanNhanVienYeuCau,
    NhanVienOnlineYeuCau,
    TrangThaiNhanVienPhanHoi,
    LuuTinNhanAIYeuCau,
    TinNhanAIPhanHoi,
)
from app.services import tro_chuyen_service
from app.utils.dependencies import get_current_customer, require_staff

router = APIRouter(prefix="/tro-chuyen", tags=["Trò chuyện"])
admin_router = APIRouter(prefix="/admin", tags=["Admin trò chuyện"])


@router.post("/send", response_model=GuiTroChuyenPhanHoi)
def gui_chat(
    payload: GuiTroChuyenYeuCau,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> GuiTroChuyenPhanHoi:
    return tro_chuyen_service.gui_tro_chuyen(db, customer, payload)


@router.post("/request-staff", response_model=GuiTroChuyenPhanHoi)
def yeu_cau_chat_nhan_vien(
    payload: NhanVienChatYeuCau,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> GuiTroChuyenPhanHoi:
    return tro_chuyen_service.yeu_cau_nhan_vien(
        db, customer, payload.conversation_id, payload.loai_yeu_cau
    )


@router.get("/staff-status", response_model=TrangThaiNhanVienPhanHoi)
def trang_thai_nhan_vien(db: Annotated[Session, Depends(get_db)]) -> TrangThaiNhanVienPhanHoi:
    return tro_chuyen_service.trang_thai_nhan_vien(db)


@router.get("/my-conversations", response_model=list[CuocTroChuyenPhanHoi])
def cuoc_tro_chuyen_cua_toi(
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> list[CuocTroChuyenPhanHoi]:
    return tro_chuyen_service.lay_cuoc_tro_chuyen_khach_hang(db, customer)


@router.get("/messages/{conversation_id}", response_model=list[TinNhanTroChuyenPhanHoi])
def tin_nhan_cuoc_tro_chuyen(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> list[TinNhanTroChuyenPhanHoi]:
    return tro_chuyen_service.lay_tin_nhan_khach_hang(db, customer, conversation_id)


@router.post("/send-staff-message", response_model=GuiTroChuyenPhanHoi)
def gui_tin_nhan_nhan_vien(
    payload: TinNhanNhanVienYeuCau,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> GuiTroChuyenPhanHoi:
    return tro_chuyen_service.gui_tin_nhan_nhan_vien_cua_khach(db, customer, payload)


@router.get("/ai/messages", response_model=list[TinNhanAIPhanHoi])
def lich_su_chat_ai(
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> list[TinNhanAIPhanHoi]:
    """Lay lich su chat AI cua khach da dang nhap (khach vang lai dung localStorage)."""
    return tro_chuyen_service.lay_lich_su_ai(db, customer)


@router.post("/ai/messages", response_model=TinNhanAIPhanHoi)
def luu_tin_nhan_chat_ai(
    payload: LuuTinNhanAIYeuCau,
    db: Annotated[Session, Depends(get_db)],
    customer: Annotated[KhachHang, Depends(get_current_customer)],
) -> TinNhanAIPhanHoi:
    """Luu 1 tin nhan (USER/AI) vao lich su chat AI cua khach da dang nhap."""
    return tro_chuyen_service.luu_tin_nhan_ai(db, customer, payload.vai_tro, payload.noi_dung)


@admin_router.get("/chat/conversations", response_model=DanhSachCuocTroChuyenAdminPhanHoi)
def cuoc_tro_chuyen_admin(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_staff)],
) -> DanhSachCuocTroChuyenAdminPhanHoi:
    return tro_chuyen_service.lay_cuoc_tro_chuyen_admin(db)


@admin_router.get("/chat/messages/{conversation_id}", response_model=list[TinNhanTroChuyenPhanHoi])
def tin_nhan_admin(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_staff)],
) -> list[TinNhanTroChuyenPhanHoi]:
    return tro_chuyen_service.lay_tin_nhan_admin(db, conversation_id)


@admin_router.post("/chat/reply", response_model=GuiTroChuyenPhanHoi)
def admin_tra_loi(
    payload: AdminTraLoiNhanVienYeuCau,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_staff)],
) -> GuiTroChuyenPhanHoi:
    return tro_chuyen_service.admin_tra_loi(db, account, payload.conversation_id, payload.message)


@admin_router.put("/chat/assign/{conversation_id}", response_model=TicketChatAdminPhanHoi)
def admin_gan_cuoc_tro_chuyen(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_staff)],
) -> TicketChatAdminPhanHoi:
    return tro_chuyen_service.gan_cuoc_tro_chuyen(db, conversation_id, account)


@admin_router.put("/chat/close/{conversation_id}", response_model=TicketChatAdminPhanHoi)
def admin_dong_cuoc_tro_chuyen(
    conversation_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_staff)],
) -> TicketChatAdminPhanHoi:
    return tro_chuyen_service.dong_cuoc_tro_chuyen(db, conversation_id)


@admin_router.put("/staff/online")
def admin_cap_nhat_nhan_vien_online(
    payload: NhanVienOnlineYeuCau,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(require_staff)],
):
    return tro_chuyen_service.cap_nhat_nhan_vien_online(db, account, payload.is_online)


legacy_router = tao_router_ke_thua(router, "/chat", tags=["Trò chuyện legacy"])
