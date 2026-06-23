import hashlib
import hmac
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Mapping
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.don_thue import ChiTietDonThue, DonThue
from app.models.tai_khoan import TaiKhoan
from app.schemas.thanh_toan import TaoThanhToanVnpayYeuCau
from app.services import (
    don_thue_service,
    gui_email_service,
    het_han_thanh_toan_service,
    thong_bao_service,
)
from app.utils.config import get_settings

logger = logging.getLogger(__name__)

MUI_GIO_VIET_NAM = timezone(timedelta(hours=7))
MA_GIAO_DICH_PATTERN = re.compile(
    r"^(?:DH)?0*(?P<id_don_thue>\d+)(?:_(?P<timestamp>\d{14,20}))?$",
    re.IGNORECASE,
)
TRANG_THAI_CHO_THANH_TOAN = "Cho thanh toan"
TRANG_THAI_DA_XAC_NHAN = "Da xac nhan"
TRANG_THAI_GIU_NGUYEN_SAU_THANH_TOAN = {
    TRANG_THAI_DA_XAC_NHAN,
    "Dang thue",
    "Da thue",
    "Da qua han",
}


@dataclass
class KetQuaXuLyVnpay:
    thanh_cong: bool
    chu_ky_hop_le: bool
    thong_bao: str
    id_don_thue: int | None
    so_tien: Decimal | None
    ma_giao_dich: str | None
    ma_phan_hoi: str | None
    trang_thai_giao_dich: str | None
    ngay_thanh_toan: datetime | None
    da_cap_nhat_he_thong: bool
    ma_phan_hoi_ipn: str = "00"

    def thanh_dict(self) -> dict:
        return {
            "thanh_cong": self.thanh_cong,
            "chu_ky_hop_le": self.chu_ky_hop_le,
            "thong_bao": self.thong_bao,
            "id_don_thue": self.id_don_thue,
            "so_tien": self.so_tien,
            "ma_giao_dich": self.ma_giao_dich,
            "ma_phan_hoi": self.ma_phan_hoi,
            "trang_thai_giao_dich": self.trang_thai_giao_dich,
            "ngay_thanh_toan": self.ngay_thanh_toan,
            "da_cap_nhat_he_thong": self.da_cap_nhat_he_thong,
        }


def _tham_so_duoc_ky(params: Mapping[str, str]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in params.items()
        if key not in {"vnp_SecureHash", "vnp_SecureHashType"}
        and value not in (None, "")
    }


def _du_lieu_ky_vnpay(params: Mapping[str, str]) -> str:
    return urlencode(sorted(_tham_so_duoc_ky(params).items()))


def tao_chu_ky_vnpay(params: Mapping[str, str], khoa_bi_mat: str) -> str:
    return hmac.new(
        khoa_bi_mat.encode("utf-8"),
        _du_lieu_ky_vnpay(params).encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()


def kiem_tra_chu_ky_vnpay(params: Mapping[str, str], khoa_bi_mat: str) -> bool:
    chu_ky_nhan_duoc = str(params.get("vnp_SecureHash", ""))
    if not chu_ky_nhan_duoc or not khoa_bi_mat:
        return False
    chu_ky_mong_doi = tao_chu_ky_vnpay(params, khoa_bi_mat)
    return hmac.compare_digest(
        chu_ky_mong_doi.lower(),
        chu_ky_nhan_duoc.lower(),
    )


def _dam_bao_cau_hinh_vnpay():
    settings = get_settings()
    if not settings.vnpay_tmn_code or not settings.vnpay_hash_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VNPAY chưa được cấu hình đầy đủ trên máy chủ.",
        )
    return settings


def _lay_id_don_thue(txn_ref: str) -> int | None:
    match = MA_GIAO_DICH_PATTERN.fullmatch(str(txn_ref or "").strip())
    return int(match.group("id_don_thue")) if match else None


def _lay_don_thue_day_du_cho_email(
    db: Session,
    id_don_thue: int,
) -> DonThue | None:
    return db.scalar(
        select(DonThue)
        .options(
            selectinload(DonThue.customer),
            selectinload(DonThue.details).selectinload(ChiTietDonThue.device),
        )
        .where(DonThue.id_don_thue == id_don_thue)
    )


def _lay_so_tien(params: Mapping[str, str]) -> Decimal | None:
    try:
        return Decimal(str(params.get("vnp_Amount", "0"))) / Decimal("100")
    except (InvalidOperation, ValueError):
        return None


def _ma_giao_dich(params: Mapping[str, str]) -> str | None:
    return (
        params.get("vnp_TransactionNo")
        or params.get("vnp_BankTranNo")
        or None
    )


def _lay_ngay_thanh_toan(params: Mapping[str, str]) -> datetime | None:
    value = str(params.get("vnp_PayDate", "")).strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def _thoi_gian_viet_nam_khong_mui_gio() -> datetime:
    return datetime.now(MUI_GIO_VIET_NAM).replace(tzinfo=None)


def tao_duong_dan_thanh_toan_vnpay(
    db: Session,
    payload: TaoThanhToanVnpayYeuCau,
    account: TaiKhoan,
    dia_chi_ip: str,
) -> str:
    settings = _dam_bao_cau_hinh_vnpay()
    tien_coc = Decimal(str(settings.vnpay_deposit_amount))
    if payload.so_tien != tien_coc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Số tiền thanh toán phải đúng {int(tien_coc):,} đồng tiền cọc.",
        )

    rental = don_thue_service.lay_don_thue_vnpay_cho_thanh_toan(
        db,
        payload.id_don_thue,
        account,
        khoa_du_lieu=True,
    )
    now = _thoi_gian_viet_nam_khong_mui_gio()
    if not rental.han_thanh_toan_vnpay:
        rental.han_thanh_toan_vnpay = now + timedelta(
            minutes=settings.vnpay_payment_expire_minutes
        )
    if rental.han_thanh_toan_vnpay <= now:
        het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(
            db,
            tai_thoi_diem=now,
        )
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Đơn thuê đã hết thời gian thanh toán VNPAY.",
        )

    txn_ref = f"DH{rental.id_don_thue}_{now.strftime('%Y%m%d%H%M%S%f')}"
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.vnpay_tmn_code,
        "vnp_Amount": str(int(tien_coc * 100)),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": txn_ref,
        "vnp_OrderInfo": payload.noi_dung_thanh_toan.strip(),
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": settings.vnpay_return_url,
        "vnp_IpAddr": dia_chi_ip or "127.0.0.1",
        "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
        "vnp_ExpireDate": rental.han_thanh_toan_vnpay.strftime("%Y%m%d%H%M%S"),
    }
    params["vnp_SecureHash"] = tao_chu_ky_vnpay(
        params,
        settings.vnpay_hash_secret,
    )

    rental.phuong_thuc_thanh_toan = "VNPAY"
    rental.so_tien_da_thanh_toan = Decimal("0")
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return f"{settings.vnpay_payment_url}?{urlencode(sorted(params.items()))}"


def _ket_qua_loi(
    *,
    thong_bao: str,
    params: Mapping[str, str],
    chu_ky_hop_le: bool,
    id_don_thue: int | None,
    so_tien: Decimal | None,
    ma_ipn: str,
) -> KetQuaXuLyVnpay:
    return KetQuaXuLyVnpay(
        thanh_cong=False,
        chu_ky_hop_le=chu_ky_hop_le,
        thong_bao=thong_bao,
        id_don_thue=id_don_thue,
        so_tien=so_tien,
        ma_giao_dich=_ma_giao_dich(params),
        ma_phan_hoi=params.get("vnp_ResponseCode"),
        trang_thai_giao_dich=params.get("vnp_TransactionStatus"),
        ngay_thanh_toan=None,
        da_cap_nhat_he_thong=False,
        ma_phan_hoi_ipn=ma_ipn,
    )


def xu_ly_giao_dich_vnpay(
    db: Session,
    params: Mapping[str, str],
    *,
    nguon: str,
) -> KetQuaXuLyVnpay:
    settings = _dam_bao_cau_hinh_vnpay()
    chu_ky_hop_le = kiem_tra_chu_ky_vnpay(
        params,
        settings.vnpay_hash_secret,
    )
    id_don_thue = _lay_id_don_thue(params.get("vnp_TxnRef", ""))
    so_tien = _lay_so_tien(params)
    ma_giao_dich = _ma_giao_dich(params)
    logger.info(
        "VNPAY %s: txn_ref=%s, don_thue=%s, response=%s, "
        "transaction_status=%s, transaction_no=%s, chu_ky_hop_le=%s",
        nguon,
        params.get("vnp_TxnRef"),
        id_don_thue,
        params.get("vnp_ResponseCode"),
        params.get("vnp_TransactionStatus"),
        ma_giao_dich,
        chu_ky_hop_le,
    )

    if not chu_ky_hop_le:
        return _ket_qua_loi(
            thong_bao="Chữ ký VNPAY không hợp lệ.",
            params=params,
            chu_ky_hop_le=False,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="97",
        )
    if params.get("vnp_TmnCode") != settings.vnpay_tmn_code:
        return _ket_qua_loi(
            thong_bao="Mã website VNPAY không hợp lệ.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="97",
        )
    if not id_don_thue:
        return _ket_qua_loi(
            thong_bao="Mã tham chiếu đơn thuê không hợp lệ.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=None,
            so_tien=so_tien,
            ma_ipn="01",
        )

    rental = db.scalar(
        select(DonThue)
        .where(DonThue.id_don_thue == id_don_thue)
        .with_for_update()
    )
    if not rental:
        return _ket_qua_loi(
            thong_bao="Không tìm thấy đơn thuê tương ứng.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="01",
        )
    if rental.phuong_thuc_thanh_toan != "VNPAY":
        return _ket_qua_loi(
            thong_bao="Đơn thuê không sử dụng phương thức thanh toán VNPAY.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="02",
        )

    tien_coc = Decimal(str(settings.vnpay_deposit_amount))
    if so_tien != tien_coc:
        return _ket_qua_loi(
            thong_bao="Số tiền VNPAY trả về không khớp tiền cọc.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="04",
        )
    if (
        params.get("vnp_ResponseCode") != "00"
        or params.get("vnp_TransactionStatus") != "00"
    ):
        return _ket_qua_loi(
            thong_bao="Thanh toán VNPAY không thành công hoặc đã bị hủy.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="00",
        )
    if not ma_giao_dich:
        return _ket_qua_loi(
            thong_bao="VNPAY không trả về mã giao dịch.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="99",
        )

    ngay_thanh_toan = (
        _lay_ngay_thanh_toan(params)
        or _thoi_gian_viet_nam_khong_mui_gio()
    )
    da_tu_dong_huy = (
        rental.trang_thai == "Da huy"
        and het_han_thanh_toan_service.la_don_tu_dong_huy_do_het_han_vnpay(
            rental
        )
    )
    if rental.han_thanh_toan_vnpay and ngay_thanh_toan > rental.han_thanh_toan_vnpay:
        return _ket_qua_loi(
            thong_bao="Giao dịch được thực hiện sau thời hạn thanh toán của đơn.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="02",
        )
    if rental.trang_thai == "Da huy" and not da_tu_dong_huy:
        return _ket_qua_loi(
            thong_bao="Đơn thuê đã bị hủy trước khi thanh toán.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="02",
        )
    if (
        rental.ma_giao_dich_vnpay
        and rental.ma_giao_dich_vnpay != ma_giao_dich
    ):
        return _ket_qua_loi(
            thong_bao="Đơn thuê đã được ghi nhận bằng giao dịch VNPAY khác.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="02",
        )

    da_ghi_nhan = (
        rental.ma_giao_dich_vnpay == ma_giao_dich
        and Decimal(rental.so_tien_da_thanh_toan or 0) == tien_coc
    )
    chuyen_sang_da_xac_nhan = rental.trang_thai in {
        TRANG_THAI_CHO_THANH_TOAN,
        "Da dat",
    } or da_tu_dong_huy

    try:
        rental.phuong_thuc_thanh_toan = "VNPAY"
        rental.ma_giao_dich_vnpay = ma_giao_dich
        rental.so_tien_da_thanh_toan = tien_coc
        rental.ngay_thanh_toan = rental.ngay_thanh_toan or ngay_thanh_toan
        if chuyen_sang_da_xac_nhan:
            rental.trang_thai = TRANG_THAI_DA_XAC_NHAN
            het_han_thanh_toan_service.bo_ghi_chu_tu_dong_huy_vnpay(rental)
        elif rental.trang_thai not in TRANG_THAI_GIU_NGUYEN_SAU_THANH_TOAN:
            return _ket_qua_loi(
                thong_bao="Trạng thái đơn thuê không cho phép ghi nhận thanh toán.",
                params=params,
                chu_ky_hop_le=True,
                id_don_thue=id_don_thue,
                so_tien=so_tien,
                ma_ipn="02",
            )

        db.add(rental)
        don_thue_service.dong_bo_trang_thai_tu_don_thue_xuong_chi_tiet(
            db,
            rental,
            rental.trang_thai,
        )
        if chuyen_sang_da_xac_nhan and not da_ghi_nhan:
            thong_bao_service.them_thong_bao_trang_thai_don(db, rental)
        db.commit()
        db.refresh(rental)
    except Exception:
        db.rollback()
        logger.exception(
            "Không thể cập nhật giao dịch VNPAY cho đơn thuê #%s.",
            id_don_thue,
        )
        return _ket_qua_loi(
            thong_bao="Không thể cập nhật giao dịch VNPAY vào cơ sở dữ liệu.",
            params=params,
            chu_ky_hop_le=True,
            id_don_thue=id_don_thue,
            so_tien=so_tien,
            ma_ipn="99",
        )

    logger.info(
        "Đã ghi nhận VNPAY cho đơn thuê #%s: trạng_thái=%s, mã_giao_dịch=%s.",
        rental.id_don_thue,
        rental.trang_thai,
        rental.ma_giao_dich_vnpay,
    )
    if not da_ghi_nhan:
        try:
            don_thue_gui_email = _lay_don_thue_day_du_cho_email(
                db,
                rental.id_don_thue,
            )
            if don_thue_gui_email:
                gui_email_service.gui_email_thong_bao_dat_thue_cho_khach_hang(
                    don_thue=don_thue_gui_email,
                    khach_hang=don_thue_gui_email.customer,
                    danh_sach_chi_tiet=don_thue_gui_email.details,
                )
                gui_email_service.gui_email_thong_bao_don_thue_moi_cho_admin(
                    don_thue=don_thue_gui_email,
                    khach_hang=don_thue_gui_email.customer,
                    danh_sach_chi_tiet=don_thue_gui_email.details,
                )
        except Exception:
            logger.exception(
                "Không thể chuẩn bị email sau thanh toán VNPAY cho đơn thuê #%s.",
                rental.id_don_thue,
            )
    return KetQuaXuLyVnpay(
        thanh_cong=True,
        chu_ky_hop_le=True,
        thong_bao="Thanh toán cọc qua VNPAY thành công.",
        id_don_thue=rental.id_don_thue,
        so_tien=tien_coc,
        ma_giao_dich=ma_giao_dich,
        ma_phan_hoi=params.get("vnp_ResponseCode"),
        trang_thai_giao_dich=params.get("vnp_TransactionStatus"),
        ngay_thanh_toan=rental.ngay_thanh_toan,
        da_cap_nhat_he_thong=True,
        ma_phan_hoi_ipn="02" if da_ghi_nhan else "00",
    )


def xu_ly_ket_qua_vnpay(db: Session, params: Mapping[str, str]) -> dict:
    return xu_ly_giao_dich_vnpay(
        db,
        params,
        nguon="RETURN",
    ).thanh_dict()


def xu_ly_ipn_vnpay(db: Session, params: Mapping[str, str]) -> dict[str, str]:
    ket_qua = xu_ly_giao_dich_vnpay(
        db,
        params,
        nguon="IPN",
    )
    messages = {
        "00": "Confirm Success",
        "01": "Order not found",
        "02": "Order already confirmed or invalid status",
        "04": "Invalid Amount",
        "97": "Invalid Checksum",
        "99": "Unknown error",
    }
    return {
        "RspCode": ket_qua.ma_phan_hoi_ipn,
        "Message": messages.get(ket_qua.ma_phan_hoi_ipn, "Unknown error"),
    }
