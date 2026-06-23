import html
import importlib
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email.utils import parseaddr
from math import ceil
from types import ModuleType
from typing import Any, Iterable

from app.utils.config import get_settings

logger = logging.getLogger(__name__)
ma_email_resend_gan_nhat: str | None = None

DIA_CHI_CUA_HANG = "382 Hùng Vương, Thanh Khê, Đà Nẵng"
SO_DIEN_THOAI_CUA_HANG = "0906 586 982"

TEN_TRANG_THAI = {
    "Cho thanh toan": "Chờ thanh toán",
    "Da dat": "Đã đặt",
    "Da xac nhan": "Đã xác nhận",
    "Dang thue": "Đang thuê",
    "Da thue": "Đã thuê",
    "Da huy": "Đã hủy",
    "Da qua han": "Đã quá hạn",
}

TEN_PHUONG_THUC_THANH_TOAN = {
    "VNPAY": "VNPAY",
    "Chuyen khoan thu cong": "Chuyển khoản thủ công",
}


def nap_thu_vien_resend() -> ModuleType | None:
    try:
        return importlib.import_module("resend")
    except ModuleNotFoundError as exc:
        if exc.name != "resend":
            raise
        logger.error(
            "Chưa cài thư viện resend. "
            "Hãy chạy '.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt'."
        )
        return None


def lay_loi_cau_hinh_email(settings: Any | None = None) -> str | None:
    if nap_thu_vien_resend() is None:
        return (
            "Chưa cài thư viện resend trong môi trường Python đang chạy. "
            "Vui lòng khởi động backend bằng Backend\\.venv\\Scripts\\python.exe."
        )

    settings = settings or get_settings()
    if not settings.resend_api_key.strip():
        return "RESEND_API_KEY chưa được cấu hình trên máy chủ."
    if not settings.email_from.strip():
        return "EMAIL_FROM chưa được cấu hình trên máy chủ."
    if not settings.email_admin.strip():
        return "EMAIL_ADMIN chưa được cấu hình trên máy chủ."
    return None


def _che_dia_chi_email(dia_chi: str) -> str:
    dia_chi = (dia_chi or "").strip()
    if "@" not in dia_chi:
        return "không xác định"
    ten, ten_mien = dia_chi.rsplit("@", 1)
    return f"{ten[:2]}***@{ten_mien}"


def _la_nguoi_gui_thu_nghiem_resend(email_from: str) -> bool:
    dia_chi = parseaddr(email_from or "")[1].lower()
    return dia_chi.endswith("@resend.dev")


def _xac_dinh_nguoi_nhan_resend(
    settings: Any,
    nguoi_nhan: str,
    tieu_de: str,
    noi_dung_html: str,
) -> tuple[str | None, str, str]:
    if not _la_nguoi_gui_thu_nghiem_resend(settings.email_from):
        return nguoi_nhan, tieu_de, noi_dung_html

    nguoi_nhan_thu_nghiem = (
        getattr(settings, "resend_test_recipient", "") or settings.email_admin
    ).strip()
    if not nguoi_nhan_thu_nghiem:
        logger.error(
            "EMAIL_FROM đang dùng miền thử nghiệm resend.dev nhưng chưa cấu hình "
            "RESEND_TEST_RECIPIENT hoặc EMAIL_ADMIN."
        )
        return None, tieu_de, noi_dung_html

    if nguoi_nhan.lower() == nguoi_nhan_thu_nghiem.lower():
        return nguoi_nhan, tieu_de, noi_dung_html

    nguoi_nhan_da_che = _che_dia_chi_email(nguoi_nhan)
    logger.warning(
        "Resend sandbox: chuyển email dự kiến gửi tới %s về địa chỉ kiểm thử %s.",
        nguoi_nhan_da_che,
        _che_dia_chi_email(nguoi_nhan_thu_nghiem),
    )
    tieu_de_thu_nghiem = f"[TEST cho {nguoi_nhan_da_che}] {tieu_de}"
    thong_bao_thu_nghiem = (
        '<div style="margin-bottom:18px;padding:12px 14px;'
        'background:#fff7ed;border-left:4px solid #f97316">'
        "Môi trường thử nghiệm Resend: email này được chuyển về hộp thư kiểm thử. "
        f"Người nhận dự kiến: {_chuoi_an_toan(nguoi_nhan_da_che)}."
        "</div>"
    )
    return (
        nguoi_nhan_thu_nghiem,
        tieu_de_thu_nghiem,
        thong_bao_thu_nghiem + noi_dung_html,
    )


def _chuoi_an_toan(gia_tri: Any, mac_dinh: str = "Chưa cập nhật") -> str:
    if gia_tri is None:
        return html.escape(mac_dinh)
    chuoi = str(gia_tri).strip()
    return html.escape(chuoi or mac_dinh)


def _dinh_dang_ngay(gia_tri: datetime | None) -> str:
    if not gia_tri:
        return "Chưa cập nhật"
    return gia_tri.strftime("%d/%m/%Y %H:%M")


def _dinh_dang_tien(gia_tri: Any) -> str:
    try:
        so_tien = Decimal(str(gia_tri or 0))
    except (InvalidOperation, TypeError, ValueError):
        so_tien = Decimal("0")
    return f"{so_tien:,.0f}".replace(",", ".") + " đ"


def _so_ngay_thue(ngay_nhan: datetime | None, ngay_tra: datetime | None) -> int:
    if not ngay_nhan or not ngay_tra:
        return 1
    return max(1, ceil((ngay_tra - ngay_nhan).total_seconds() / 86400))


def _danh_sach_chi_tiet(danh_sach_chi_tiet: Iterable[Any] | None) -> list[Any]:
    return list(danh_sach_chi_tiet or [])


def _ngay_nhan_va_ngay_tra(danh_sach_chi_tiet: Iterable[Any] | None) -> tuple[datetime | None, datetime | None]:
    danh_sach = _danh_sach_chi_tiet(danh_sach_chi_tiet)
    cac_ngay_nhan = [
        chi_tiet.ngay_nhan
        for chi_tiet in danh_sach
        if getattr(chi_tiet, "ngay_nhan", None)
    ]
    cac_ngay_tra = [
        chi_tiet.ngay_tra
        for chi_tiet in danh_sach
        if getattr(chi_tiet, "ngay_tra", None)
    ]
    return (
        min(cac_ngay_nhan) if cac_ngay_nhan else None,
        max(cac_ngay_tra) if cac_ngay_tra else None,
    )


def _tao_cac_dong_thiet_bi(danh_sach_chi_tiet: Iterable[Any] | None) -> str:
    cac_dong: list[str] = []
    for chi_tiet in _danh_sach_chi_tiet(danh_sach_chi_tiet):
        thiet_bi = getattr(chi_tiet, "device", None)
        ten_thiet_bi = getattr(thiet_bi, "ten_thiet_bi", None) or (
            f"Thiết bị #{getattr(chi_tiet, 'id_thiet_bi', '')}"
        )
        so_luong = int(getattr(chi_tiet, "so_luong", 0) or 0)
        gia_thue = getattr(chi_tiet, "gia_thue", 0)
        ngay_nhan = getattr(chi_tiet, "ngay_nhan", None)
        ngay_tra = getattr(chi_tiet, "ngay_tra", None)
        thanh_tien = (
            Decimal(str(gia_thue or 0))
            * so_luong
            * _so_ngay_thue(ngay_nhan, ngay_tra)
        )
        cac_dong.append(
            f"""
            <tr>
                <td>{_chuoi_an_toan(ten_thiet_bi)}</td>
                <td style="text-align:center">{so_luong}</td>
                <td>{_dinh_dang_ngay(ngay_nhan)}</td>
                <td>{_dinh_dang_ngay(ngay_tra)}</td>
                <td style="text-align:right">{_dinh_dang_tien(gia_thue)}</td>
                <td style="text-align:right">{_dinh_dang_tien(thanh_tien)}</td>
            </tr>
            """
        )

    if cac_dong:
        return "".join(cac_dong)
    return """
        <tr>
            <td colspan="6" style="text-align:center;color:#64748b">
                Chưa có thông tin thiết bị.
            </td>
        </tr>
    """


def _khung_email(tieu_de: str, noi_dung: str) -> str:
    return f"""
    <!doctype html>
    <html lang="vi">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
      </head>
      <body style="margin:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#0f172a">
        <div style="max-width:760px;margin:0 auto;padding:24px">
          <div style="background:#0f172a;color:#fff;padding:22px 28px;border-radius:14px 14px 0 0">
            <div style="font-size:24px;font-weight:700">SunLens Camera</div>
            <div style="margin-top:6px;color:#cbd5e1">{_chuoi_an_toan(tieu_de)}</div>
          </div>
          <div style="background:#fff;padding:28px;border-radius:0 0 14px 14px">
            {noi_dung}
          </div>
          <div style="padding:16px;text-align:center;color:#64748b;font-size:12px">
            Email được gửi tự động từ hệ thống SunLens Camera.
          </div>
        </div>
      </body>
    </html>
    """


def _bang_thiet_bi(danh_sach_chi_tiet: Iterable[Any] | None) -> str:
    return f"""
    <div style="overflow-x:auto;margin:20px 0">
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <thead>
          <tr style="background:#e2e8f0">
            <th style="padding:10px;text-align:left">Thiết bị</th>
            <th style="padding:10px;text-align:center">Số lượng</th>
            <th style="padding:10px;text-align:left">Ngày nhận</th>
            <th style="padding:10px;text-align:left">Ngày trả</th>
            <th style="padding:10px;text-align:right">Giá/ngày</th>
            <th style="padding:10px;text-align:right">Thành tiền</th>
          </tr>
        </thead>
        <tbody>{_tao_cac_dong_thiet_bi(danh_sach_chi_tiet)}</tbody>
      </table>
    </div>
    """


def _dong_thong_tin(nhan: str, gia_tri: Any) -> str:
    return (
        '<tr>'
        f'<td style="padding:7px 12px 7px 0;color:#64748b">{_chuoi_an_toan(nhan)}</td>'
        f'<td style="padding:7px 0;font-weight:600">{_chuoi_an_toan(gia_tri)}</td>'
        '</tr>'
    )


def gui_email(nguoi_nhan: str, tieu_de: str, noi_dung_html: str) -> bool:
    global ma_email_resend_gan_nhat
    try:
        settings = get_settings()
        thu_vien_resend = nap_thu_vien_resend()
        nguoi_nhan = (nguoi_nhan or "").strip()
        if not nguoi_nhan:
            logger.warning("Bỏ qua gửi email vì không có địa chỉ người nhận.")
            return False
        if thu_vien_resend is None:
            logger.error("Không thể gửi email vì chưa cài thư viện resend.")
            return False
        if not settings.resend_api_key.strip():
            logger.warning("Bỏ qua gửi email vì thiếu RESEND_API_KEY.")
            return False
        if not settings.email_from.strip():
            logger.warning("Bỏ qua gửi email vì thiếu EMAIL_FROM.")
            return False

        nguoi_nhan_thuc_te, tieu_de_thuc_te, noi_dung_thuc_te = (
            _xac_dinh_nguoi_nhan_resend(
                settings,
                nguoi_nhan,
                tieu_de,
                noi_dung_html,
            )
        )
        if not nguoi_nhan_thuc_te:
            return False

        thu_vien_resend.api_key = settings.resend_api_key
        phan_hoi = thu_vien_resend.Emails.send(
            {
                "from": settings.email_from,
                "to": [nguoi_nhan_thuc_te],
                "subject": tieu_de_thuc_te,
                "html": noi_dung_thuc_te,
            }
        )
        ma_email_resend_gan_nhat = (
            getattr(phan_hoi, "id", None)
            or (phan_hoi.get("id") if isinstance(phan_hoi, dict) else None)
        )
        logger.info(
            "Đã gửi email '%s' đến %s, mã Resend=%s.",
            tieu_de_thuc_te,
            nguoi_nhan_thuc_te,
            ma_email_resend_gan_nhat,
        )
        return True
    except Exception:
        ma_email_resend_gan_nhat = None
        logger.exception("Không thể gửi email '%s' đến %s qua Resend.", tieu_de, nguoi_nhan)
        return False


def tao_noi_dung_email_dat_thue_cho_khach_hang(
    don_thue: Any,
    khach_hang: Any,
    danh_sach_chi_tiet: Iterable[Any],
) -> str:
    ngay_nhan, ngay_tra = _ngay_nhan_va_ngay_tra(danh_sach_chi_tiet)
    ma_don = f"DH{don_thue.id_don_thue}"
    trang_thai = TEN_TRANG_THAI.get(
        getattr(don_thue, "trang_thai", None),
        getattr(don_thue, "trang_thai", None),
    )
    phuong_thuc = TEN_PHUONG_THUC_THANH_TOAN.get(
        getattr(don_thue, "phuong_thuc_thanh_toan", None),
        getattr(don_thue, "phuong_thuc_thanh_toan", None),
    )
    noi_dung = f"""
      <p>Xin chào <strong>{_chuoi_an_toan(getattr(khach_hang, "ho_ten", None), "Quý khách")}</strong>,</p>
      <p>SunLens Camera đã nhận đơn thuê của bạn. Thông tin đơn như sau:</p>
      <table style="border-collapse:collapse">
        {_dong_thong_tin("Mã đơn thuê", ma_don)}
        {_dong_thong_tin("Ngày đặt", _dinh_dang_ngay(getattr(don_thue, "ngay_dat", None)))}
        {_dong_thong_tin("Ngày nhận", _dinh_dang_ngay(ngay_nhan))}
        {_dong_thong_tin("Ngày trả", _dinh_dang_ngay(ngay_tra))}
        {_dong_thong_tin("Phương thức thanh toán", phuong_thuc)}
        {_dong_thong_tin("Trạng thái", trang_thai)}
      </table>
      {_bang_thiet_bi(danh_sach_chi_tiet)}
      <table style="margin-left:auto;border-collapse:collapse">
        {_dong_thong_tin("Tổng tiền thuê", _dinh_dang_tien(getattr(don_thue, "tong_tien", 0)))}
        {_dong_thong_tin("Đã thanh toán/đặt cọc", _dinh_dang_tien(getattr(don_thue, "so_tien_da_thanh_toan", 0)))}
      </table>
      <div style="margin-top:22px;padding:14px 16px;background:#eff6ff;border-left:4px solid #2563eb">
        SunLens Camera sẽ liên hệ xác nhận đơn thuê trong thời gian sớm nhất.
      </div>
    """
    return _khung_email(f"Xác nhận đã nhận đơn thuê {ma_don}", noi_dung)


def tao_noi_dung_email_don_thue_moi_cho_admin(
    don_thue: Any,
    khach_hang: Any,
    danh_sach_chi_tiet: Iterable[Any],
) -> str:
    ngay_nhan, ngay_tra = _ngay_nhan_va_ngay_tra(danh_sach_chi_tiet)
    ma_don = f"DH{don_thue.id_don_thue}"
    trang_thai = TEN_TRANG_THAI.get(
        getattr(don_thue, "trang_thai", None),
        getattr(don_thue, "trang_thai", None),
    )
    phuong_thuc = TEN_PHUONG_THUC_THANH_TOAN.get(
        getattr(don_thue, "phuong_thuc_thanh_toan", None),
        getattr(don_thue, "phuong_thuc_thanh_toan", None),
    )
    noi_dung = f"""
      <p>Hệ thống vừa ghi nhận một đơn thuê mới.</p>
      <table style="border-collapse:collapse">
        {_dong_thong_tin("Mã đơn thuê", ma_don)}
        {_dong_thong_tin("Tên khách hàng", getattr(khach_hang, "ho_ten", None))}
        {_dong_thong_tin("Số điện thoại", getattr(khach_hang, "sdt", None))}
        {_dong_thong_tin("Email", getattr(khach_hang, "email", None))}
        {_dong_thong_tin("Địa chỉ", getattr(khach_hang, "dia_chi", None))}
        {_dong_thong_tin("Ngày nhận", _dinh_dang_ngay(ngay_nhan))}
        {_dong_thong_tin("Ngày trả", _dinh_dang_ngay(ngay_tra))}
        {_dong_thong_tin("Phương thức thanh toán", phuong_thuc)}
        {_dong_thong_tin("Trạng thái", trang_thai)}
      </table>
      {_bang_thiet_bi(danh_sach_chi_tiet)}
      <table style="margin-left:auto;border-collapse:collapse">
        {_dong_thong_tin("Tổng tiền", _dinh_dang_tien(getattr(don_thue, "tong_tien", 0)))}
        {_dong_thong_tin("Đã thanh toán/đặt cọc", _dinh_dang_tien(getattr(don_thue, "so_tien_da_thanh_toan", 0)))}
      </table>
      <div style="margin-top:22px;padding:14px 16px;background:#fff7ed;border-left:4px solid #f97316">
        Vui lòng vào trang quản trị SunLens Camera để kiểm tra và xác nhận đơn.
      </div>
    """
    return _khung_email(f"Có đơn thuê mới {ma_don}", noi_dung)


def tao_noi_dung_email_don_thue_da_xac_nhan_cho_khach_hang(
    don_thue: Any,
    khach_hang: Any,
    danh_sach_chi_tiet: Iterable[Any],
) -> str:
    ngay_nhan, _ = _ngay_nhan_va_ngay_tra(danh_sach_chi_tiet)
    ma_don = f"DH{don_thue.id_don_thue}"
    noi_dung = f"""
      <p>Xin chào <strong>{_chuoi_an_toan(getattr(khach_hang, "ho_ten", None), "Quý khách")}</strong>,</p>
      <p>Đơn thuê <strong>{_chuoi_an_toan(ma_don)}</strong> đã được SunLens Camera xác nhận.</p>
      <table style="border-collapse:collapse">
        {_dong_thong_tin("Ngày nhận thiết bị", _dinh_dang_ngay(ngay_nhan))}
        {_dong_thong_tin("Địa chỉ cửa hàng", DIA_CHI_CUA_HANG)}
        {_dong_thong_tin("Số điện thoại liên hệ", SO_DIEN_THOAI_CUA_HANG)}
      </table>
      <div style="margin-top:22px;padding:14px 16px;background:#ecfdf5;border-left:4px solid #10b981">
        Cảm ơn bạn đã lựa chọn SunLens Camera.
      </div>
    """
    return _khung_email(f"Đơn thuê {ma_don} đã được xác nhận", noi_dung)


def tao_noi_dung_email_dat_lai_mat_khau(
    khach_hang: Any,
    link_dat_lai: str,
    thoi_han_phut: int,
) -> str:
    noi_dung = f"""
      <p>Xin chào <strong>{_chuoi_an_toan(getattr(khach_hang, "ho_ten", None), "Quý khách")}</strong>,</p>
      <p>SunLens Camera đã nhận yêu cầu đặt lại mật khẩu cho tài khoản của bạn.</p>
      <div style="margin:22px 0">
        <a
          href="{_chuoi_an_toan(link_dat_lai)}"
          style="display:inline-block;padding:12px 20px;background:#2563eb;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:700"
        >
          Đặt lại mật khẩu
        </a>
      </div>
      <p>Liên kết này có hiệu lực trong <strong>{_chuoi_an_toan(thoi_han_phut)}</strong> phút.</p>
      <p>Nếu nút không hoạt động, vui lòng sao chép và mở liên kết sau:</p>
      <p style="word-break:break-all;color:#2563eb">{_chuoi_an_toan(link_dat_lai)}</p>
      <div style="margin-top:22px;padding:14px 16px;background:#fff7ed;border-left:4px solid #f97316">
        Nếu bạn không gửi yêu cầu này, bạn có thể bỏ qua email và mật khẩu hiện tại sẽ không bị thay đổi.
      </div>
    """
    return _khung_email("Yêu cầu đặt lại mật khẩu", noi_dung)


def gui_email_thong_bao_dat_thue_cho_khach_hang(
    don_thue: Any,
    khach_hang: Any,
    danh_sach_chi_tiet: Iterable[Any],
) -> bool:
    try:
        email_khach_hang = (getattr(khach_hang, "email", None) or "").strip()
        if not email_khach_hang:
            logger.info(
                "Bỏ qua email khách hàng cho đơn thuê #%s vì khách chưa có email.",
                getattr(don_thue, "id_don_thue", None),
            )
            return False
        return gui_email(
            email_khach_hang,
            f"SunLens Camera - Xác nhận đã nhận đơn thuê DH{don_thue.id_don_thue}",
            tao_noi_dung_email_dat_thue_cho_khach_hang(
                don_thue,
                khach_hang,
                danh_sach_chi_tiet,
            ),
        )
    except Exception:
        logger.exception(
            "Không thể chuẩn bị email đặt thuê cho khách của đơn #%s.",
            getattr(don_thue, "id_don_thue", None),
        )
        return False


def gui_email_thong_bao_don_thue_moi_cho_admin(
    don_thue: Any,
    khach_hang: Any,
    danh_sach_chi_tiet: Iterable[Any],
) -> bool:
    try:
        email_admin = get_settings().email_admin.strip()
        if not email_admin:
            logger.warning(
                "Bỏ qua email admin cho đơn thuê #%s vì thiếu EMAIL_ADMIN.",
                getattr(don_thue, "id_don_thue", None),
            )
            return False
        return gui_email(
            email_admin,
            f"SunLens Camera - Có đơn thuê mới DH{don_thue.id_don_thue}",
            tao_noi_dung_email_don_thue_moi_cho_admin(
                don_thue,
                khach_hang,
                danh_sach_chi_tiet,
            ),
        )
    except Exception:
        logger.exception(
            "Không thể chuẩn bị email đơn thuê mới #%s cho admin.",
            getattr(don_thue, "id_don_thue", None),
        )
        return False


def gui_email_thong_bao_don_thue_da_xac_nhan_cho_khach_hang(
    don_thue: Any,
    khach_hang: Any,
    danh_sach_chi_tiet: Iterable[Any],
) -> bool:
    try:
        email_khach_hang = (getattr(khach_hang, "email", None) or "").strip()
        if not email_khach_hang:
            logger.info(
                "Bỏ qua email xác nhận đơn #%s vì khách chưa có email.",
                getattr(don_thue, "id_don_thue", None),
            )
            return False
        return gui_email(
            email_khach_hang,
            f"SunLens Camera - Đơn thuê DH{don_thue.id_don_thue} đã được xác nhận",
            tao_noi_dung_email_don_thue_da_xac_nhan_cho_khach_hang(
                don_thue,
                khach_hang,
                danh_sach_chi_tiet,
            ),
        )
    except Exception:
        logger.exception(
            "Không thể chuẩn bị email xác nhận đơn #%s cho khách.",
            getattr(don_thue, "id_don_thue", None),
        )
        return False
