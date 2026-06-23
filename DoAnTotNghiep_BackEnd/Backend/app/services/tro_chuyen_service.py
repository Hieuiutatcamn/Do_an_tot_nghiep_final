from datetime import datetime, timedelta
from typing import Any
import unicodedata

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.cuoc_tro_chuyen import (
    CuocTroChuyen,
    TinNhanCuocTroChuyen,
    PhieuChat,
    NhanVienOnline,
    TinNhanAI,
)
from app.models.khach_hang import KhachHang
from app.models.nhan_vien import NhanVien
from app.schemas.tro_chuyen import GuiTroChuyenYeuCau, TinNhanNhanVienYeuCau

OPEN_CHAT_STATUSES = {"CHO_NHAN_VIEN", "NHAN_VIEN_DANG_XU_LY"}
STAFF_ONLINE_WINDOW_MINUTES = 5
# Loai ticket hop le (khop enum LOAI_VE_CHAT trong models/hang_so.py)
LOAI_VE_CHAT_HOP_LE = {"KHIEU_NAI", "HUY_DON", "HOAN_TIEN", "CAN_XAC_NHAN", "KHAC"}
TRANG_THAI_TICKET_CHAT_MO = {"MOI", "DANG_XU_LY"}
NOI_DUNG_YEU_CAU_MAC_DINH = "Yêu cầu hỗ trợ từ khách hàng."


def khoa_chuan_hoa_ticket_chat(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower().replace("-", "_").replace(" ", "_")
    while "__" in ascii_value:
        ascii_value = ascii_value.replace("__", "_")
    return ascii_value.strip("_")


def chuan_hoa_trang_thai_ticket_chat(
    ticket_status: str | None,
    conversation_status: str | None = None,
) -> str:
    status_key = khoa_chuan_hoa_ticket_chat(ticket_status)
    conversation_key = khoa_chuan_hoa_ticket_chat(conversation_status)
    mapping = {
        "moi": "MOI",
        "cho_nhan_vien": "MOI",
        "online": "MOI",
        "chuyen_nhan_vien": "MOI",
        "waiting_staff": "MOI",
        "dang_xu_ly": "DANG_XU_LY",
        "nhan_vien_dang_xu_ly": "DANG_XU_LY",
        "in_progress": "DANG_XU_LY",
        "da_xu_ly": "DA_XU_LY",
        "dong": "DA_XU_LY",
        "da_dong": "DA_XU_LY",
        "closed": "DA_XU_LY",
    }
    if status_key in mapping:
        return mapping[status_key]
    if conversation_key in mapping:
        return mapping[conversation_key]
    return "MOI"


def chuan_hoa_yeu_cau_ticket_chat(value: str | None) -> str | None:
    request_key = khoa_chuan_hoa_ticket_chat(value)
    mapping = {
        "hoi_san_pham": "hoi_san_pham",
        "hoi_gia_thue": "hoi_gia_thue",
        "hoi_don_thue": "hoi_don_thue",
        "khieu_nai": "khieu_nai",
        "hoan_tien": "hoan_tien",
        "huy_don": "huy_don",
        "can_nhan_vien": "can_nhan_vien",
        "can_nhan_vien_ho_tro": "can_nhan_vien",
        "can_xac_nhan": "can_nhan_vien",
        "khac": "khac",
    }
    return mapping.get(request_key)


def lay_ticket_chat_uu_tien(conversation: CuocTroChuyen) -> PhieuChat | None:
    tickets = list(conversation.tickets or [])
    if not tickets:
        return None

    def sap_xep(items: list[PhieuChat]) -> PhieuChat:
        return sorted(
            items,
            key=lambda item: (item.created_at or datetime.min, item.id_ticket or 0),
            reverse=True,
        )[0]

    tickets_mo = [ticket for ticket in tickets if ticket.trang_thai in TRANG_THAI_TICKET_CHAT_MO]
    return sap_xep(tickets_mo) if tickets_mo else sap_xep(tickets)


def lay_tin_nhan_khach_dau_tien(conversation: CuocTroChuyen) -> str | None:
    messages = sorted(
        list(conversation.messages or []),
        key=lambda item: (item.created_at or datetime.min, item.id_tin_nhan or 0),
    )
    for message in messages:
        if message.sender_type == "CUSTOMER":
            noi_dung = str(message.noi_dung or "").strip()
            if noi_dung:
                return noi_dung
    return None


def lay_noi_dung_yeu_cau_ticket_chat(
    conversation: CuocTroChuyen,
    ticket: PhieuChat | None,
) -> str | None:
    candidates = [
        ticket.noi_dung if ticket else None,
        conversation.chu_de,
        lay_tin_nhan_khach_dau_tien(conversation),
    ]
    for candidate in candidates:
        normalized = str(candidate or "").strip()
        if normalized and normalized != NOI_DUNG_YEU_CAU_MAC_DINH:
            return normalized
    return str(ticket.noi_dung).strip() if ticket and ticket.noi_dung else None


def dong_bo_trang_thai_ticket_chat(
    db: Session,
    conversation: CuocTroChuyen,
    trang_thai_moi: str,
) -> PhieuChat | None:
    ticket = lay_ticket_chat_uu_tien(conversation)
    if not ticket:
        return None
    ticket.trang_thai = trang_thai_moi
    db.add(ticket)
    db.flush()
    return ticket


def gui_tro_chuyen(
    db: Session,
    customer: KhachHang,
    payload: GuiTroChuyenYeuCau | TinNhanNhanVienYeuCau,
) -> dict[str, Any]:
    if payload.conversation_id:
        conversation = lay_cuoc_tro_chuyen_hoac_404(db, payload.conversation_id)
        if conversation.id_khach_hang != customer.id_khach_hang:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể truy cập cuộc trò chuyện này")
        if conversation.trang_thai == "DA_DONG":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuộc trò chuyện đã đóng")
    else:
        conversation = lay_hoac_tao_cuoc_tro_chuyen_mo(db, customer)

    user_message = them_tin_nhan_chat(
        db,
        conversation,
        "CUSTOMER",
        customer.id_khach_hang,
        payload.message,
    )
    gan_nhan_vien_kha_dung(db, conversation)

    staff_online = bool(conversation.id_nhan_vien)
    if staff_online:
        conversation.need_staff = False
        message = "Đã gửi yêu cầu hỗ trợ."
    else:
        conversation.need_staff = True
        conversation.trang_thai = "CHO_NHAN_VIEN"
        tao_phieu_chat(db, conversation, payload.message)
        message = "Nhân viên sẽ phản hồi bạn sớm nhất."

    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    db.refresh(user_message)

    return {
        "success": True,
        "staff_online": staff_online,
        "message": message,
        "conversation": cuoc_tro_chuyen_sang_dict(conversation),
        "user_message": tin_nhan_sang_dict(user_message),
        "reply_message": None,
        "messages": [tin_nhan_sang_dict(user_message)],
    }


def yeu_cau_nhan_vien(
    db: Session,
    customer: KhachHang,
    conversation_id: int | None = None,
    loai_yeu_cau: str | None = None,
) -> dict[str, Any]:
    if conversation_id:
        conversation = lay_cuoc_tro_chuyen_hoac_404(db, conversation_id)
        if conversation.id_khach_hang != customer.id_khach_hang:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể truy cập cuộc trò chuyện này")
        if conversation.trang_thai == "DA_DONG":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cuộc trò chuyện đã đóng")
    else:
        conversation = lay_hoac_tao_cuoc_tro_chuyen_mo(db, customer)

    conversation.chat_mode = "STAFF"
    conversation.need_staff = True
    conversation.trang_thai = "CHO_NHAN_VIEN"

    gan_nhan_vien_kha_dung(db, conversation)

    # Luon ghi nhan ticket cho moi yeu cau ho tro (idempotent theo cuoc tro chuyen):
    # nho do AI escalate luon tao ticket dung loai, du nhan vien online hay offline.
    loai_ve = loai_yeu_cau if loai_yeu_cau in LOAI_VE_CHAT_HOP_LE else "KHAC"
    ticket = tao_phieu_chat(db, conversation, "Yêu cầu hỗ trợ từ khách hàng.", loai_ve)
    ticket_id = ticket.id_ticket if ticket else None

    if conversation.id_nhan_vien:
        message = "Đã kết nối với nhân viên hỗ trợ."
        staff_online = True
    else:
        message = "Nhân viên hiện offline, hệ thống đã ghi nhận yêu cầu của bạn."
        staff_online = False

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "success": True,
        "staff_online": staff_online,
        "message": message,
        "ticket_id": ticket_id,
        "conversation": cuoc_tro_chuyen_sang_dict(conversation),
        "messages": [],
    }


def trang_thai_nhan_vien(db: Session) -> dict[str, object]:
    online = lay_nhan_vien_kha_dung(db) is not None
    return {
        "staff_online": online,
        "online": online,
        "message": "Nhân viên đang online" if online else "Nhân viên hiện offline",
    }


def lay_cuoc_tro_chuyen_khach_hang(db: Session, customer: KhachHang) -> list[dict[str, Any]]:
    conversations = db.scalars(
        select(CuocTroChuyen)
        .options(
            selectinload(CuocTroChuyen.customer),
            selectinload(CuocTroChuyen.employee),
            selectinload(CuocTroChuyen.messages),
        )
        .where(CuocTroChuyen.id_khach_hang == customer.id_khach_hang)
        .order_by(CuocTroChuyen.updated_at.desc(), CuocTroChuyen.id_cuoc_tro_chuyen.desc())
    ).all()
    return [cuoc_tro_chuyen_sang_dict(conversation) for conversation in conversations]


def lay_tin_nhan_khach_hang(db: Session, customer: KhachHang, conversation_id: int) -> list[dict[str, Any]]:
    conversation = lay_cuoc_tro_chuyen_hoac_404(db, conversation_id)
    if conversation.id_khach_hang != customer.id_khach_hang:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể truy cập cuộc trò chuyện này")
    if danh_dau_tin_nhan_nhan_vien_da_doc(conversation):
        db.add(conversation)
        db.commit()
    return lay_danh_sach_tin_nhan(db, conversation_id)


def gui_tin_nhan_nhan_vien_cua_khach(db: Session, customer: KhachHang, payload: TinNhanNhanVienYeuCau) -> dict[str, Any]:
    return gui_tro_chuyen(db, customer, payload)


def lay_cuoc_tro_chuyen_admin(db: Session) -> dict[str, Any]:
    conversations = db.scalars(
        select(CuocTroChuyen)
        .options(
            selectinload(CuocTroChuyen.customer),
            selectinload(CuocTroChuyen.employee),
            selectinload(CuocTroChuyen.messages),
            selectinload(CuocTroChuyen.tickets),
        )
        .order_by(
            (CuocTroChuyen.trang_thai == "CHO_NHAN_VIEN").desc(),
            CuocTroChuyen.updated_at.desc(),
            CuocTroChuyen.id_cuoc_tro_chuyen.desc(),
        )
    ).all()
    waiting_count = sum(1 for conversation in conversations if cuoc_tro_chuyen_can_xu_ly(conversation))
    unread_message_count = sum(dem_tin_nhan_khach_chua_doc(conversation) for conversation in conversations)
    return {
        "items": [ticket_chat_admin_sang_dict(conversation, waiting_count=waiting_count) for conversation in conversations],
        "waiting_count": waiting_count,
        "unread_message_count": unread_message_count,
    }


def lay_tin_nhan_admin(db: Session, conversation_id: int) -> list[dict[str, Any]]:
    conversation = lay_cuoc_tro_chuyen_hoac_404(db, conversation_id)
    changed = danh_dau_tin_nhan_khach_da_doc(conversation)
    if conversation.need_staff:
        conversation.need_staff = False
        changed = True
    if changed:
        db.add(conversation)
        db.commit()
    return lay_danh_sach_tin_nhan(db, conversation_id)


def gan_cuoc_tro_chuyen(db: Session, conversation_id: int, account: TaiKhoan) -> dict[str, Any]:
    employee = lay_nhan_vien_theo_tai_khoan(account, required=True)
    conversation = lay_cuoc_tro_chuyen_hoac_404(db, conversation_id)
    conversation.id_nhan_vien = employee.id_nhan_vien
    conversation.need_staff = False
    conversation.trang_thai = "NHAN_VIEN_DANG_XU_LY"
    danh_dau_tin_nhan_khach_da_doc(conversation)
    dong_bo_trang_thai_ticket_chat(db, conversation, "DANG_XU_LY")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ticket_chat_admin_sang_dict(conversation)


def dong_cuoc_tro_chuyen(db: Session, conversation_id: int) -> dict[str, Any]:
    conversation = lay_cuoc_tro_chuyen_hoac_404(db, conversation_id)
    conversation.trang_thai = "DA_DONG"
    conversation.need_staff = False
    dong_bo_trang_thai_ticket_chat(db, conversation, "DA_XU_LY")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ticket_chat_admin_sang_dict(conversation)


def admin_tra_loi(db: Session, account: TaiKhoan, conversation_id: int, message: str) -> dict[str, Any]:
    conversation = lay_cuoc_tro_chuyen_hoac_404(db, conversation_id)
    employee = lay_nhan_vien_theo_tai_khoan(account, required=False)
    if employee and not conversation.id_nhan_vien:
        conversation.id_nhan_vien = employee.id_nhan_vien
    if conversation.trang_thai != "DA_DONG":
        conversation.trang_thai = "NHAN_VIEN_DANG_XU_LY"
        dong_bo_trang_thai_ticket_chat(db, conversation, "DANG_XU_LY")
    conversation.need_staff = False
    danh_dau_tin_nhan_khach_da_doc(conversation)
    staff_message = them_tin_nhan_chat(
        db,
        conversation,
        "STAFF",
        employee.id_nhan_vien if employee else account.id_tai_khoan,
        message,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    db.refresh(staff_message)
    return {
        "success": True,
        "message": "Đã gửi tin nhắn.",
        "conversation": cuoc_tro_chuyen_sang_dict(conversation),
        "reply_message": tin_nhan_sang_dict(staff_message),
        "messages": [tin_nhan_sang_dict(staff_message)],
    }


def cap_nhat_nhan_vien_online(db: Session, account: TaiKhoan, is_online: bool) -> dict[str, Any]:
    employee = lay_nhan_vien_theo_tai_khoan(account, required=True)
    status_row = db.scalar(
        select(NhanVienOnline).where(NhanVienOnline.id_nhan_vien == employee.id_nhan_vien)
    )
    if not status_row:
        status_row = NhanVienOnline(id_nhan_vien=employee.id_nhan_vien)
    status_row.is_online = is_online
    status_row.last_seen = datetime.utcnow()
    db.add(status_row)
    db.commit()
    db.refresh(status_row)
    return {
        "staff_online": status_row.is_online,
        "id_nhan_vien": employee.id_nhan_vien,
    }


def lay_hoac_tao_cuoc_tro_chuyen_mo(db: Session, customer: KhachHang) -> CuocTroChuyen:
    conversation = db.scalar(
        select(CuocTroChuyen)
        .options(selectinload(CuocTroChuyen.messages))
        .where(
            CuocTroChuyen.id_khach_hang == customer.id_khach_hang,
            CuocTroChuyen.trang_thai.in_(OPEN_CHAT_STATUSES),
        )
        .order_by(CuocTroChuyen.updated_at.desc(), CuocTroChuyen.id_cuoc_tro_chuyen.desc())
    )
    if conversation:
        return conversation

    conversation = CuocTroChuyen(
        id_khach_hang=customer.id_khach_hang,
        chat_mode="STAFF",
        trang_thai="CHO_NHAN_VIEN",
        need_staff=True,
    )
    db.add(conversation)
    db.flush()
    return conversation


def them_tin_nhan_chat(
    db: Session,
    conversation: CuocTroChuyen,
    sender_type: str,
    sender_id: int | None,
    content: str,
) -> TinNhanCuocTroChuyen:
    normalized_content = str(content or "").strip()
    if not normalized_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nội dung tin nhắn không được trống")
    if sender_type not in {"CUSTOMER", "STAFF"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loại người gửi không hợp lệ")
    if sender_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không xác định được người gửi tin nhắn")

    message = TinNhanCuocTroChuyen(
        id_cuoc_tro_chuyen=conversation.id_cuoc_tro_chuyen,
        sender_type=sender_type,
        sender_id=sender_id,
        noi_dung=normalized_content,
        loai_tin_nhan="TEXT",
    )
    conversation.updated_at = datetime.utcnow()
    db.add(message)
    db.add(conversation)
    db.flush()
    return message


def lay_cuoc_tro_chuyen_hoac_404(db: Session, conversation_id: int) -> CuocTroChuyen:
    conversation = db.scalar(
        select(CuocTroChuyen)
        .options(
            selectinload(CuocTroChuyen.customer),
            selectinload(CuocTroChuyen.employee),
            selectinload(CuocTroChuyen.messages),
            selectinload(CuocTroChuyen.tickets),
        )
        .where(CuocTroChuyen.id_cuoc_tro_chuyen == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy cuộc trò chuyện")
    return conversation


def lay_danh_sach_tin_nhan(db: Session, conversation_id: int) -> list[dict[str, Any]]:
    messages = db.scalars(
        select(TinNhanCuocTroChuyen)
        .where(TinNhanCuocTroChuyen.id_cuoc_tro_chuyen == conversation_id)
        .order_by(TinNhanCuocTroChuyen.created_at.asc(), TinNhanCuocTroChuyen.id_tin_nhan.asc())
    ).all()
    return [tin_nhan_sang_dict(message) for message in messages]


def lay_nhan_vien_kha_dung(db: Session) -> NhanVien | None:
    cutoff = datetime.utcnow() - timedelta(minutes=STAFF_ONLINE_WINDOW_MINUTES)
    return db.scalar(
        select(NhanVien)
        .join(NhanVienOnline, NhanVienOnline.id_nhan_vien == NhanVien.id_nhan_vien)
        .where(
            NhanVienOnline.is_online.is_(True),
            NhanVienOnline.last_seen >= cutoff,
        )
        .order_by(NhanVienOnline.last_seen.desc(), NhanVien.id_nhan_vien.asc())
    )


def gan_nhan_vien_kha_dung(db: Session, conversation: CuocTroChuyen) -> None:
    if conversation.id_nhan_vien:
        conversation.trang_thai = "NHAN_VIEN_DANG_XU_LY"
        return

    employee = lay_nhan_vien_kha_dung(db)
    if employee:
        conversation.id_nhan_vien = employee.id_nhan_vien
        conversation.trang_thai = "NHAN_VIEN_DANG_XU_LY"


def dem_tin_nhan_khach_chua_doc(conversation: CuocTroChuyen) -> int:
    return sum(
        1
        for message in conversation.messages or []
        if message.sender_type == "CUSTOMER" and not message.da_doc
    )


def cuoc_tro_chuyen_can_xu_ly(conversation: CuocTroChuyen) -> bool:
    return (
        bool(conversation.need_staff)
        or dem_tin_nhan_khach_chua_doc(conversation) > 0
    )


def danh_dau_tin_nhan_khach_da_doc(conversation: CuocTroChuyen) -> bool:
    changed = False
    for message in conversation.messages or []:
        if message.sender_type == "CUSTOMER" and not message.da_doc:
            message.da_doc = True
            changed = True
    return changed


def danh_dau_tin_nhan_nhan_vien_da_doc(conversation: CuocTroChuyen) -> bool:
    changed = False
    for message in conversation.messages or []:
        if message.sender_type == "STAFF" and not message.da_doc:
            message.da_doc = True
            changed = True
    return changed


def tao_phieu_chat(
    db: Session,
    conversation: CuocTroChuyen,
    content: str,
    ticket_type: str = "KHAC",
) -> PhieuChat:
    existing_ticket = db.scalar(
        select(PhieuChat).where(
            PhieuChat.id_cuoc_tro_chuyen == conversation.id_cuoc_tro_chuyen,
            PhieuChat.trang_thai.in_(["MOI", "DANG_XU_LY"]),
        )
    )
    if existing_ticket:
        return existing_ticket

    ticket = PhieuChat(
        id_cuoc_tro_chuyen=conversation.id_cuoc_tro_chuyen,
        id_khach_hang=conversation.id_khach_hang,
        loai_ticket=ticket_type,
        noi_dung=content,
        trang_thai="MOI",
    )
    db.add(ticket)
    db.flush()
    return ticket


def luu_tin_nhan_ai(db: Session, customer: KhachHang, vai_tro: str, noi_dung: str) -> TinNhanAI:
    """Luu 1 tin nhan vao lich su chat AI (khach da dang nhap)."""
    tin_nhan = TinNhanAI(
        id_khach_hang=customer.id_khach_hang,
        vai_tro=vai_tro if vai_tro in ("USER", "AI") else "USER",
        noi_dung=noi_dung,
    )
    db.add(tin_nhan)
    db.commit()
    db.refresh(tin_nhan)
    return tin_nhan


def lay_lich_su_ai(db: Session, customer: KhachHang, limit: int = 30) -> list[TinNhanAI]:
    """Lay lich su chat AI gan nhat cua khach (theo thu tu cu -> moi)."""
    rows = db.scalars(
        select(TinNhanAI)
        .where(TinNhanAI.id_khach_hang == customer.id_khach_hang)
        .order_by(TinNhanAI.id_tin_nhan_ai.desc())
        .limit(limit)
    ).all()
    return list(reversed(rows))


def lay_nhan_vien_theo_tai_khoan(account: TaiKhoan, required: bool) -> NhanVien | None:
    if account.employee:
        return account.employee
    if required:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hồ sơ nhân viên là bắt buộc để thực hiện hành động này",
        )
    return None


def cuoc_tro_chuyen_sang_dict(
    conversation: CuocTroChuyen,
    waiting_count: int | None = None,
) -> dict[str, Any]:
    messages = sorted(
        list(conversation.messages or []),
        key=lambda item: (item.created_at or datetime.min, item.id_tin_nhan or 0),
    )
    last_message = messages[-1].noi_dung if messages else None
    unread_customer_count = dem_tin_nhan_khach_chua_doc(conversation)
    return {
        "id_cuoc_tro_chuyen": conversation.id_cuoc_tro_chuyen,
        "id_khach_hang": conversation.id_khach_hang,
        "id_nhan_vien": conversation.id_nhan_vien,
        "chat_mode": conversation.chat_mode,
        "trang_thai": conversation.trang_thai,
        "chu_de": conversation.chu_de,
        "need_staff": conversation.need_staff,
        "can_nhan_vien": conversation.need_staff,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "customer_name": conversation.customer.ho_ten if conversation.customer else None,
        "employee_name": conversation.employee.ho_ten if conversation.employee else None,
        "last_message": last_message,
        "waiting_count": waiting_count,
        "unread_customer_count": unread_customer_count,
        "so_tin_nhan_khach_chua_doc": unread_customer_count,
    }


def ticket_chat_admin_sang_dict(
    conversation: CuocTroChuyen,
    waiting_count: int | None = None,
) -> dict[str, Any]:
    conversation_data = cuoc_tro_chuyen_sang_dict(conversation, waiting_count=waiting_count)
    ticket = lay_ticket_chat_uu_tien(conversation)
    yeu_cau = chuan_hoa_yeu_cau_ticket_chat(ticket.loai_ticket if ticket else None)
    noi_dung_yeu_cau = lay_noi_dung_yeu_cau_ticket_chat(conversation, ticket)
    if not yeu_cau:
        yeu_cau = "khac" if noi_dung_yeu_cau else None

    conversation_data.update(
        {
            "id_ticket_chat": ticket.id_ticket if ticket else None,
            "loai_chat": conversation.chat_mode,
            "trang_thai": chuan_hoa_trang_thai_ticket_chat(
                ticket.trang_thai if ticket else None,
                conversation.trang_thai,
            ),
            "trang_thai_cuoc_tro_chuyen": conversation.trang_thai,
            "yeu_cau": yeu_cau,
            "noi_dung_yeu_cau": noi_dung_yeu_cau,
            "nhan_vien_phu_trach": conversation.employee.ho_ten if conversation.employee else None,
            "ngay_cap_nhat": conversation.updated_at,
        }
    )
    return conversation_data


def tin_nhan_sang_dict(message: TinNhanCuocTroChuyen) -> dict[str, Any]:
    return {
        "id_tin_nhan": message.id_tin_nhan,
        "id_cuoc_tro_chuyen": message.id_cuoc_tro_chuyen,
        "sender_type": message.sender_type,
        "sender_id": message.sender_id,
        "noi_dung": message.noi_dung,
        "loai_tin_nhan": message.loai_tin_nhan,
        "da_doc": message.da_doc,
        "created_at": message.created_at,
    }
