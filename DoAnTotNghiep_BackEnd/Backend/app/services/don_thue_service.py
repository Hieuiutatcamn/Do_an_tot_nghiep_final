import logging
from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import TRANG_THAI_DON_HANG, VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN
from app.models.khach_hang import KhachHang
from app.models.thiet_bi import ThietBi
from app.models.don_thue import DonThue, ChiTietDonThue
from app.schemas.don_thue import (
    ChiTietDonThuePhanHoi,
    DonThueTao,
    TrangThaiChiTietDonThueCapNhat,
    TrangThaiDonThueCapNhat,
)
from app.services import (
    gio_hang_service,
    gui_email_service,
    khach_hang_service,
    kiem_tra_lich_thue_service,
    ma_giam_gia_service,
    thong_bao_service,
)
from app.services import het_han_thanh_toan_service
from app.utils.config import get_settings
from app.utils.pagination import PaginationParams

TRANG_THAI_CHO_THANH_TOAN = "Cho thanh toan"
TRANG_THAI_DA_DAT = "Da dat"
TRANG_THAI_DA_XAC_NHAN = "Da xac nhan"
PHUONG_THUC_VNPAY = "VNPAY"
PHUONG_THUC_CHUYEN_KHOAN_THU_CONG = "Chuyen khoan thu cong"
TIEN_COC_THU_CONG = Decimal("200000")
logger = logging.getLogger(__name__)
TRANG_THAI_DON_THUE_CO_THE_HUY = {
    TRANG_THAI_CHO_THANH_TOAN,
    TRANG_THAI_DA_DAT,
    "Da xac nhan",
}
TRANG_THAI_DON_THUE_DA_HUY = "Da huy"
BAO_LOI_TRANG_THAI_DON_THUE = "Chỉ được cập nhật đơn thuê đang chờ xác nhận."
CHUYEN_TRANG_THAI_HOP_LE = {
    TRANG_THAI_CHO_THANH_TOAN: {"Da huy"},
    TRANG_THAI_DA_DAT: {TRANG_THAI_DA_XAC_NHAN, "Da huy"},
    TRANG_THAI_DA_XAC_NHAN: {"Dang thue", "Da huy"},
    "Dang thue": {"Da thue", "Da qua han"},
    "Da qua han": {"Da thue"},
    "Da thue": set(),
    "Da huy": set(),
}
CAC_GIA_TRI_TRANG_THAI_CHI_TIET = TRANG_THAI_DON_HANG


def cap_nhat_so_tien_da_thanh_toan_thu_cong(rental: DonThue) -> None:
    if rental.phuong_thuc_thanh_toan == PHUONG_THUC_VNPAY:
        return

    rental.phuong_thuc_thanh_toan = PHUONG_THUC_CHUYEN_KHOAN_THU_CONG
    so_tien_hien_tai = rental.so_tien_da_thanh_toan or Decimal("0")
    if so_tien_hien_tai < TIEN_COC_THU_CONG:
        rental.so_tien_da_thanh_toan = TIEN_COC_THU_CONG


def _ngay_thue(start: datetime, end: datetime) -> int:
    seconds = (end - start).total_seconds()
    return max(1, ceil(seconds / 86400))


def _xem_toan_bo(account: TaiKhoan) -> bool:
    return account.vai_tro in {VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN}


def _lay_cac_trang_thai_co_the_chuyen(trang_thai_hien_tai: str | None) -> set[str]:
    return CHUYEN_TRANG_THAI_HOP_LE.get(trang_thai_hien_tai or "", set())


def _bao_loi_chuyen_trang_thai_khong_hop_le(
    trang_thai_hien_tai: str | None,
    trang_thai_moi: str,
    doi_tuong: str,
) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"Không thể chuyển trạng thái {doi_tuong} từ "
            f"'{trang_thai_hien_tai}' sang '{trang_thai_moi}'."
        ),
    )


def lay_chi_tiet_don_thue_hoac_404(
    db: Session,
    id_chi_tiet_don_thue: int,
    *,
    khoa_du_lieu: bool = False,
) -> ChiTietDonThue:
    truy_van = (
        select(ChiTietDonThue)
        .options(selectinload(ChiTietDonThue.device))
        .where(ChiTietDonThue.id_chi_tiet_don_thue == id_chi_tiet_don_thue)
    )
    if khoa_du_lieu:
        truy_van = truy_van.with_for_update()
    chi_tiet = db.scalar(truy_van)
    if not chi_tiet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy chi tiết đơn thuê",
        )
    return chi_tiet


def lay_danh_sach_chi_tiet_don_thue(
    db: Session,
    id_don_thue: int,
    *,
    khoa_du_lieu: bool = False,
) -> list[ChiTietDonThue]:
    truy_van = (
        select(ChiTietDonThue)
        .options(selectinload(ChiTietDonThue.device))
        .where(ChiTietDonThue.id_don_thue == id_don_thue)
        .order_by(ChiTietDonThue.id_chi_tiet_don_thue.asc())
    )
    if khoa_du_lieu:
        truy_van = truy_van.with_for_update()
    return list(db.scalars(truy_van).all())


def dong_bo_trang_thai_tu_don_thue_xuong_chi_tiet(
    db: Session,
    don_thue: DonThue,
    trang_thai_moi: str | None = None,
) -> list[ChiTietDonThue]:
    trang_thai_can_dong_bo = trang_thai_moi or don_thue.trang_thai
    danh_sach_chi_tiet = lay_danh_sach_chi_tiet_don_thue(
        db,
        don_thue.id_don_thue,
        khoa_du_lieu=True,
    )
    for chi_tiet in danh_sach_chi_tiet:
        chi_tiet.trang_thai = trang_thai_can_dong_bo
        db.add(chi_tiet)
    return danh_sach_chi_tiet


def kiem_tra_tat_ca_chi_tiet_cung_trang_thai(
    danh_sach_chi_tiet: list[ChiTietDonThue],
) -> str | None:
    if not danh_sach_chi_tiet:
        return None
    trang_thai_dau_tien = danh_sach_chi_tiet[0].trang_thai
    if all(chi_tiet.trang_thai == trang_thai_dau_tien for chi_tiet in danh_sach_chi_tiet):
        return trang_thai_dau_tien
    return None


def cap_nhat_trang_thai_don_thue_noi_bo(
    db: Session,
    don_thue: DonThue,
    trang_thai_moi: str,
    *,
    tao_thong_bao_trang_thai: bool = False,
    bo_ghi_chu_tu_dong_huy_vnpay: bool = False,
) -> str:
    trang_thai_hien_tai = don_thue.trang_thai
    if trang_thai_moi == trang_thai_hien_tai:
        return str(trang_thai_hien_tai or "")

    cac_trang_thai_hop_le = _lay_cac_trang_thai_co_the_chuyen(trang_thai_hien_tai)
    if trang_thai_moi not in cac_trang_thai_hop_le:
        _bao_loi_chuyen_trang_thai_khong_hop_le(
            trang_thai_hien_tai,
            trang_thai_moi,
            "đơn thuê",
        )

    if (
        trang_thai_hien_tai == TRANG_THAI_DA_DAT
        and trang_thai_moi == TRANG_THAI_DA_XAC_NHAN
    ):
        cap_nhat_so_tien_da_thanh_toan_thu_cong(don_thue)

    don_thue.trang_thai = trang_thai_moi
    if bo_ghi_chu_tu_dong_huy_vnpay:
        het_han_thanh_toan_service.bo_ghi_chu_tu_dong_huy_vnpay(don_thue)
    db.add(don_thue)
    dong_bo_trang_thai_tu_don_thue_xuong_chi_tiet(db, don_thue, trang_thai_moi)
    if tao_thong_bao_trang_thai:
        thong_bao_service.them_thong_bao_trang_thai_don(db, don_thue)
    return str(trang_thai_hien_tai or "")


def _gui_email_xac_nhan_don_thue(don_thue_da_cap_nhat: DonThue) -> None:
    try:
        gui_email_service.gui_email_thong_bao_don_thue_da_xac_nhan_cho_khach_hang(
            don_thue=don_thue_da_cap_nhat,
            khach_hang=don_thue_da_cap_nhat.customer,
            danh_sach_chi_tiet=don_thue_da_cap_nhat.details,
        )
    except Exception:
        logger.exception(
            "Không thể chuẩn bị email xác nhận đơn thuê #%s.",
            don_thue_da_cap_nhat.id_don_thue,
        )


def _so_luong_thue_trung_lich(
    danh_sach_cho_xu_ly: list[tuple[int, datetime, datetime, int]],
    id_thiet_bi: int,
    start: datetime,
    end: datetime,
) -> int:
    return sum(
        quantity
        for pending_id_thiet_bi, pending_start, pending_end, quantity in danh_sach_cho_xu_ly
        if pending_id_thiet_bi == id_thiet_bi and pending_start < end and pending_end > start
    )


def dong_bo_ho_so_khach_hang_khi_dat_thue(
    db: Session,
    customer_id: int,
    payload: DonThueTao,
    account: TaiKhoan,
) -> KhachHang:
    customer = db.scalar(
        select(KhachHang)
        .where(KhachHang.id_khach_hang == customer_id)
        .with_for_update()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin khách hàng.",
        )

    if _xem_toan_bo(account) and payload.thong_tin_khach_hang_tu_thanh_toan is None:
        return customer

    return khach_hang_service.cap_nhat_thong_tin_khach_hang_tu_thanh_toan(
        db,
        customer,
        payload.thong_tin_khach_hang_tu_thanh_toan,
    )


def tao_don_thue(
    db: Session,
    payload: DonThueTao,
    account: TaiKhoan,
) -> DonThue:
    het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(db)
    customer_id = payload.id_khach_hang if _xem_toan_bo(account) and payload.id_khach_hang else None
    if not customer_id:
        if not account.customer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không tìm thấy thông tin khách hàng.")
        customer_id = account.customer.id_khach_hang

    try:
        dong_bo_ho_so_khach_hang_khi_dat_thue(db, customer_id, payload, account)
        should_clear_cart = gio_hang_service.gio_hang_khop_muc_don_thue(db, customer_id, payload.items)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Thông tin hồ sơ khách hàng đã được sử dụng bởi khách hàng khác.",
        ) from exc

    phuong_thuc_thanh_toan = payload.phuong_thuc_thanh_toan
    if not phuong_thuc_thanh_toan and payload.anh_chuyen_khoan:
        phuong_thuc_thanh_toan = "Chuyen khoan thu cong"
    la_thanh_toan_vnpay = phuong_thuc_thanh_toan == "VNPAY"
    trang_thai_ban_dau = (
        TRANG_THAI_CHO_THANH_TOAN
        if la_thanh_toan_vnpay
        else TRANG_THAI_DA_DAT
    )
    han_thanh_toan_vnpay = None
    if la_thanh_toan_vnpay:
        han_thanh_toan_vnpay = datetime.now() + timedelta(
            minutes=get_settings().vnpay_payment_expire_minutes
        )

    order = DonThue(
        id_khach_hang=customer_id,
        trang_thai=trang_thai_ban_dau,
        tong_tien=Decimal("0"),
        anh_chuyen_khoan=payload.anh_chuyen_khoan,
        phuong_thuc_thanh_toan=phuong_thuc_thanh_toan,
        so_tien_da_thanh_toan=Decimal("0"),
        han_thanh_toan_vnpay=han_thanh_toan_vnpay,
        ghi_chu=payload.ghi_chu,
    )
    db.add(order)
    db.flush()
   
    total = Decimal("0")
    total_days = 0
    try:
        validated_items: list[tuple[Any, ThietBi]] = []
        danh_sach_cho_xu_ly: list[tuple[int, datetime, datetime, int]] = []
        for item in payload.items:
            device = db.get(ThietBi, item.id_thiet_bi, with_for_update=True)
            if not device:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ThietBi {item.id_thiet_bi} Không tồn tại")

            pending_overlap_quantity = _so_luong_thue_trung_lich(
                danh_sach_cho_xu_ly,
                device.id_thiet_bi,
                item.ngay_nhan,
                item.ngay_tra,
            )
            kiem_tra_lich_thue_service.dam_bao_kha_dung(
                db,
                device,
                item.ngay_nhan,
                item.ngay_tra,
                item.so_luong,
                extra_reserved_quantity=pending_overlap_quantity,
            )
            danh_sach_cho_xu_ly.append((device.id_thiet_bi, item.ngay_nhan, item.ngay_tra, item.so_luong))
            validated_items.append((item, device))

        for item, device in validated_items:
            unit_price = Decimal(device.gia_thue or 0)
            days = _ngay_thue(item.ngay_nhan, item.ngay_tra)
            total_days += days
            total += unit_price * item.so_luong * days

            detail = ChiTietDonThue(
                id_don_thue=order.id_don_thue,
                id_thiet_bi=device.id_thiet_bi,
                ngay_nhan=item.ngay_nhan,
                ngay_tra=item.ngay_tra,
                so_luong=item.so_luong,
                gia_thue=unit_price,
                trang_thai=trang_thai_ban_dau,
            )
            db.add(detail)

        db.flush()
        discount, discount_amount = ma_giam_gia_service.xac_thuc_ma_giam_gia_cho_don(
            db,
            total,
            total_days,
            ma_code=payload.ma_code,
            discount_id=payload.id_ma_giam_gia,
        )
        order.id_ma_giam_gia = discount.id_ma_giam_gia if discount else None
        order.so_tien_giam = discount_amount
        order.tong_tien = max(Decimal("0"), total - discount_amount)
        ma_giam_gia_service.danh_dau_ma_giam_gia_da_dung(discount)
        db.add(order)
        if discount:
            db.add(discount)
        thong_bao_service.them_thong_bao_tao_don(db, order)
        if should_clear_cart:
            gio_hang_service.xoa_gio_hang_theo_khach_hang(db, customer_id, commit=False)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Thông tin hồ sơ khách hàng đã được sử dụng bởi khách hàng khác.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Không thể lưu DON_THUE và CHI_TIET_DON_THUE")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Không thể lưu đơn thuê vào cơ sở dữ liệu. "
                "Giao dịch đã được hoàn tác."
            ),
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Không thể tạo đơn thuê")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo đơn thuê. Giao dịch đã được hoàn tác.",
        ) from exc

    don_thue_da_tao = tim_kiem_don_thue(db, order.id_don_thue, account)
    if not la_thanh_toan_vnpay:
        try:
            gui_email_service.gui_email_thong_bao_dat_thue_cho_khach_hang(
                don_thue=don_thue_da_tao,
                khach_hang=don_thue_da_tao.customer,
                danh_sach_chi_tiet=don_thue_da_tao.details,
            )
            gui_email_service.gui_email_thong_bao_don_thue_moi_cho_admin(
                don_thue=don_thue_da_tao,
                khach_hang=don_thue_da_tao.customer,
                danh_sach_chi_tiet=don_thue_da_tao.details,
            )
        except Exception:
            logger.exception(
                "Không thể chuẩn bị email sau khi tạo đơn thuê #%s.",
                don_thue_da_tao.id_don_thue,
            )
    return don_thue_da_tao


def lay_danh_sach_don_thue(
    db: Session,
    params: PaginationParams,
    account: TaiKhoan,
    status_filter: str | None = None,
    search: str | None = None,
) -> tuple[list[DonThue], int]:
    het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(db)
    stmt = select(DonThue).options(
        selectinload(DonThue.customer),
        selectinload(DonThue.details).selectinload(ChiTietDonThue.device),
    )
    count_stmt = select(func.count()).select_from(DonThue)

    if not _xem_toan_bo(account):
        if not account.customer:
            return [], 0
        stmt = stmt.where(DonThue.id_khach_hang == account.customer.id_khach_hang)
        count_stmt = count_stmt.where(DonThue.id_khach_hang == account.customer.id_khach_hang)
    if status_filter:
        stmt = stmt.where(DonThue.trang_thai == status_filter)
        count_stmt = count_stmt.where(DonThue.trang_thai == status_filter)
    if search and search.strip():
        keyword = search.strip()
        like = f"%{keyword}%"
        digits = "".join(char for char in keyword if char.isdigit())
        search_conditions = [
            cast(DonThue.id_don_thue, String).like(like),
            cast(DonThue.ngay_dat, String).like(like),
            DonThue.trang_thai.ilike(like),
            DonThue.customer.has(
                or_(
                    KhachHang.ho_ten.ilike(like),
                    KhachHang.sdt.ilike(like),
                    KhachHang.email.ilike(like),
                )
            ),
            DonThue.details.any(
                or_(
                    cast(ChiTietDonThue.ngay_nhan, String).like(like),
                    cast(ChiTietDonThue.ngay_tra, String).like(like),
                )
            ),
        ]
        if digits:
            search_conditions.append(DonThue.id_don_thue == int(digits.lstrip("0") or "0"))

        search_filter = or_(*search_conditions)
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = db.scalar(count_stmt) or 0
    rentals = db.scalars(
        stmt.order_by(DonThue.id_don_thue.desc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(rentals), total


def tim_kiem_don_thue(db: Session, rental_id: int, account: TaiKhoan) -> DonThue:
    het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(db)
    rental = db.scalar(
        select(DonThue)
        .options(
            selectinload(DonThue.customer),
            selectinload(DonThue.details).selectinload(ChiTietDonThue.device),
        )
        .where(DonThue.id_don_thue == rental_id)
    )
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn hàng")
    if not _xem_toan_bo(account):
        if not account.customer or rental.id_khach_hang != account.customer.id_khach_hang:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập đơn hàng này")
    return rental


def lay_don_thue_cho_cap_nhat_nguoi_dung(
    db: Session,
    rental_id: int,
    account: TaiKhoan,
    *,
    khoa_du_lieu: bool = False,
) -> DonThue:
    stmt = select(DonThue).where(DonThue.id_don_thue == rental_id)
    if khoa_du_lieu:
        stmt = stmt.with_for_update()
    rental = db.scalar(stmt)

    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn hàng")
    if not account.customer or rental.id_khach_hang != account.customer.id_khach_hang:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật đơn hàng này",
        )
    if rental.trang_thai != TRANG_THAI_DA_DAT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=BAO_LOI_TRANG_THAI_DON_THUE,
        )
    return rental


def _chuan_hoa_truong_bat_buoc(value: str, field_name: str, max_length: int) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} không được trống.",
        )
    if len(normalized) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} không được vượt quá {max_length} ký tự.",
        )
    return normalized


def cap_nhat_thong_tin_don_thue_nguoi_dung(
    db: Session,
    rental_id: int,
    account: TaiKhoan,
    *,
    ho_ten: str,
    sdt: str,
    dia_chi: str,
    ghi_chu: str | None = None,
    image_path: str | None = None,
) -> DonThue:
    try:
        rental = lay_don_thue_cho_cap_nhat_nguoi_dung(
            db,
            rental_id,
            account,
            khoa_du_lieu=True,
        )
        customer = db.scalar(
            select(KhachHang)
            .where(KhachHang.id_khach_hang == rental.id_khach_hang)
            .with_for_update()
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin khách hàng.",
            )

        customer.ho_ten = _chuan_hoa_truong_bat_buoc(ho_ten, "Họ tên", 100)
        customer.sdt = _chuan_hoa_truong_bat_buoc(sdt, "Số điện thoại", 20)
        customer.dia_chi = _chuan_hoa_truong_bat_buoc(dia_chi, "Địa chỉ", 255)
        rental.ghi_chu = (ghi_chu or "").strip()[:255] or None
        if image_path:
            rental.anh_chuyen_khoan = image_path
            rental.phuong_thuc_thanh_toan = "Chuyen khoan thu cong"
            rental.so_tien_da_thanh_toan = Decimal("0")

        db.add(customer)
        db.add(rental)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Số điện thoại đã được sử dụng bởi khách hàng khác.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Không thể cập nhật thông tin đơn thuê")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể cập nhật đơn thuê. Giao dịch đã được hoàn tác.",
        ) from exc

    return tim_kiem_don_thue(db, rental_id, account)


def cap_nhat_trang_thai_don_thue(
    db: Session,
    rental_id: int,
    payload: TrangThaiDonThueCapNhat,
    account: TaiKhoan,
) -> DonThue:
    if not _xem_toan_bo(account):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền cập nhật trạng thái đơn thuê")

    het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(db)
    rental = db.scalar(
        select(DonThue)
        .where(DonThue.id_don_thue == rental_id)
        .with_for_update()
    )
    if not rental:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn hàng",
        )

    trang_thai_cu = cap_nhat_trang_thai_don_thue_noi_bo(
        db,
        rental,
        payload.trang_thai,
        tao_thong_bao_trang_thai=True,
    )
    db.commit()
    db.refresh(rental)
    don_thue_da_cap_nhat = tim_kiem_don_thue(
        db,
        rental.id_don_thue,
        account,
    )
    if (
        trang_thai_cu == TRANG_THAI_DA_DAT
        and don_thue_da_cap_nhat.trang_thai == TRANG_THAI_DA_XAC_NHAN
    ):
        _gui_email_xac_nhan_don_thue(don_thue_da_cap_nhat)
    return don_thue_da_cap_nhat


def huy_don_thue(
    db: Session,
    rental_id: int,
    account: TaiKhoan,
    reason: str | None = None,
) -> DonThue:
    rental = tim_kiem_don_thue(db, rental_id, account)

    if not _xem_toan_bo(account):
        if not account.customer or rental.id_khach_hang != account.customer.id_khach_hang:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền hủy đơn hàng này",
            )

    if rental.trang_thai not in TRANG_THAI_DON_THUE_CO_THE_HUY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đơn hàng hiện tại không thể hủy",
        )

    rental.trang_thai = TRANG_THAI_DON_THUE_DA_HUY
    if reason:
        rental.ghi_chu = f"{rental.ghi_chu or ''}\nLy do huy: {reason}".strip()[:255]

    db.add(rental)
    dong_bo_trang_thai_tu_don_thue_xuong_chi_tiet(
        db,
        rental,
        TRANG_THAI_DON_THUE_DA_HUY,
    )
    thong_bao_service.them_thong_bao_huy_don(db, rental)
    db.commit()
    db.refresh(rental)
    return tim_kiem_don_thue(db, rental.id_don_thue, account)


def dong_bo_trang_thai_tu_chi_tiet_len_don_thue(
    db: Session,
    don_thue: DonThue,
    account: TaiKhoan,
    *,
    trang_thai_muc_tieu: str,
) -> DonThue:
    if don_thue.trang_thai == trang_thai_muc_tieu:
        return tim_kiem_don_thue(db, don_thue.id_don_thue, account)

    trang_thai_cu = cap_nhat_trang_thai_don_thue_noi_bo(
        db,
        don_thue,
        trang_thai_muc_tieu,
        tao_thong_bao_trang_thai=True,
    )
    db.commit()
    db.refresh(don_thue)
    don_thue_da_cap_nhat = tim_kiem_don_thue(db, don_thue.id_don_thue, account)
    if (
        trang_thai_cu == TRANG_THAI_DA_DAT
        and don_thue_da_cap_nhat.trang_thai == TRANG_THAI_DA_XAC_NHAN
    ):
        _gui_email_xac_nhan_don_thue(don_thue_da_cap_nhat)
    return don_thue_da_cap_nhat


def cap_nhat_trang_thai_chi_tiet_don_thue(
    db: Session,
    id_chi_tiet_don_thue: int,
    payload: TrangThaiChiTietDonThueCapNhat,
    account: TaiKhoan,
) -> ChiTietDonThue:
    if not _xem_toan_bo(account):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật trạng thái chi tiết đơn thuê",
        )

    chi_tiet = lay_chi_tiet_don_thue_hoac_404(
        db,
        id_chi_tiet_don_thue,
        khoa_du_lieu=True,
    )
    if chi_tiet.id_don_thue is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chi tiết đơn thuê chưa gắn với đơn thuê hợp lệ.",
        )

    don_thue = db.scalar(
        select(DonThue)
        .where(DonThue.id_don_thue == chi_tiet.id_don_thue)
        .with_for_update()
    )
    if not don_thue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn thuê",
        )

    if payload.trang_thai == chi_tiet.trang_thai:
        db.refresh(chi_tiet)
        return chi_tiet

    cac_trang_thai_hop_le = _lay_cac_trang_thai_co_the_chuyen(chi_tiet.trang_thai)
    if payload.trang_thai not in cac_trang_thai_hop_le:
        _bao_loi_chuyen_trang_thai_khong_hop_le(
            chi_tiet.trang_thai,
            payload.trang_thai,
            "chi tiết đơn thuê",
        )

    chi_tiet.trang_thai = payload.trang_thai
    db.add(chi_tiet)
    db.flush()

    danh_sach_chi_tiet = lay_danh_sach_chi_tiet_don_thue(
        db,
        don_thue.id_don_thue,
        khoa_du_lieu=True,
    )
    trang_thai_dong_nhat = kiem_tra_tat_ca_chi_tiet_cung_trang_thai(danh_sach_chi_tiet)
    if trang_thai_dong_nhat:
        don_thue_da_cap_nhat = dong_bo_trang_thai_tu_chi_tiet_len_don_thue(
            db,
            don_thue,
            account,
            trang_thai_muc_tieu=trang_thai_dong_nhat,
        )
        chi_tiet_moi = next(
            (
                muc
                for muc in don_thue_da_cap_nhat.details
                if muc.id_chi_tiet_don_thue == id_chi_tiet_don_thue
            ),
            None,
        )
        if not chi_tiet_moi:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể tải lại chi tiết đơn thuê sau khi cập nhật.",
            )
        return chi_tiet_moi

    db.commit()
    db.refresh(chi_tiet)
    return lay_chi_tiet_don_thue_hoac_404(db, id_chi_tiet_don_thue)


def cap_nhat_anh_thanh_toan_don_thue(
    db: Session,
    rental_id: int,
    image_path: str,
    account: TaiKhoan,
) -> DonThue:
    rental = lay_don_thue_cho_cap_nhat_nguoi_dung(
        db,
        rental_id,
        account,
        khoa_du_lieu=True,
    )

    rental.anh_chuyen_khoan = image_path
    rental.phuong_thuc_thanh_toan = "Chuyen khoan thu cong"
    rental.so_tien_da_thanh_toan = Decimal("0")
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return tim_kiem_don_thue(db, rental.id_don_thue, account)


def lay_don_thue_vnpay_cho_thanh_toan(
    db: Session,
    rental_id: int,
    account: TaiKhoan,
    *,
    khoa_du_lieu: bool = False,
) -> DonThue:
    het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(db)
    stmt = select(DonThue).where(DonThue.id_don_thue == rental_id)
    if khoa_du_lieu:
        stmt = stmt.with_for_update()
    rental = db.scalar(stmt)
    if not rental:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đơn thuê.",
        )
    if not account.customer or rental.id_khach_hang != account.customer.id_khach_hang:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thanh toán đơn thuê này.",
        )
    if rental.phuong_thuc_thanh_toan != "VNPAY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đơn thuê này không sử dụng phương thức VNPAY.",
        )
    if rental.trang_thai != TRANG_THAI_CHO_THANH_TOAN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Đơn thuê không còn ở trạng thái chờ thanh toán.",
        )
    return rental
