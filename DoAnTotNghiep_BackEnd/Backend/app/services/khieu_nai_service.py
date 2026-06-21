import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.khieu_nai import KhieuNai
from app.models.hang_so import VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN
from app.models.khach_hang import KhachHang
from app.models.don_thue import DonThue, ChiTietDonThue
from app.schemas.khieu_nai import (
    DANH_SACH_TRANG_THAI_KHIEU_NAI,
    KhieuNaiTao,
    TrangThaiKhieuNaiCapNhat,
    KhieuNaiCapNhat,
)
from app.utils.pagination import PaginationParams

TRANG_THAI_KHIEU_NAI_MAC_DINH = "Cho phan hoi"


def _xem_toan_bo(account: TaiKhoan) -> bool:
    return account.vai_tro in {VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN}


def _kiem_tra_ton_tai_khach_hang(db: Session, customer_id: int | None) -> KhachHang:
    if customer_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ban cần cung cấp id_khach_hang")
    customer = db.get(KhachHang, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không tìm thấy khách hàng")
    return customer


def _lay_don_thue_kem_chi_tiet(db: Session, rental_id: int | None) -> DonThue:
    if rental_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bạn cần cung cấp id_don_thue")
    rental = db.scalar(
        select(DonThue)
        .options(selectinload(DonThue.details).selectinload(ChiTietDonThue.device))
        .where(DonThue.id_don_thue == rental_id)
    )
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn hàng")
    return rental


def _dam_bao_quyen_truy_cap(account: TaiKhoan, complaint: KhieuNai) -> None:
    if _xem_toan_bo(account):
        return
    if not account.customer or complaint.id_khach_hang != account.customer.id_khach_hang:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể truy cập khiếu nại này")


def _dam_bao_nhan_vien(account: TaiKhoan) -> None:
    if not _xem_toan_bo(account):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vai trò nhân viên hoặc admin là bắt buộc")


def _kiem_tra_trang_thai(value: str) -> str:
    normalized = (value or "").strip()
    if normalized not in DANH_SACH_TRANG_THAI_KHIEU_NAI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trạng thái khiếu nại không hợp lệ",
        )
    return normalized


def _danh_sach_ten_thiet_bi_duoc_chon(rental: DonThue, id_thiet_bis: list[int]) -> list[str]:
    requested_ids = {int(item) for item in id_thiet_bis}
    order_id_thiet_bis = {int(detail.id_thiet_bi) for detail in rental.details if detail.id_thiet_bi is not None}
    invalid_ids = requested_ids - order_id_thiet_bis
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sản phẩm khiếu nại không thuộc đơn hàng này",
        )

    names: list[str] = []
    seen_ids: set[int] = set()
    for detail in rental.details:
        if detail.id_thiet_bi is None or int(detail.id_thiet_bi) not in requested_ids:
            continue
        if int(detail.id_thiet_bi) in seen_ids:
            continue
        seen_ids.add(int(detail.id_thiet_bi))
        names.append(detail.device.ten_thiet_bi if detail.device else f"Thiết bị #{detail.id_thiet_bi}")

    if not names:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng chọn sản phẩm khiếu nại")
    return names


def khieu_nai_sang_dict_admin(complaint: KhieuNai, customer: KhachHang | None, rental: DonThue | None) -> dict[str, Any]:
    order_id = complaint.id_don_thue
    return {
        "Id_khieu_nai": complaint.id_khieu_nai,
        "id_khieu_nai": complaint.id_khieu_nai,
        "id_don_thue": order_id,
        "ma_don": f"DH{order_id:04d}" if order_id else None,
        "id_khach_hang": complaint.id_khach_hang,
        "ten_khach_hang": customer.ho_ten if customer else None,
        "sdt": customer.sdt if customer else None,
        "tieu_de": complaint.tieu_de,
        "san_pham_khieu_nai": complaint.san_pham_khieu_nai,
        "noi_dung": complaint.noi_dung,
        "trang_thai": complaint.trang_thai,
        "ngay_khieu_nai": complaint.ngay_khieu_nai,
    }


def khieu_nai_sang_dict_nguoi_dung(complaint: KhieuNai) -> dict[str, Any]:
    order_id = complaint.id_don_thue
    return {
        "Id_khieu_nai": complaint.id_khieu_nai,
        "id_khieu_nai": complaint.id_khieu_nai,
        "id_don_thue": order_id,
        "ma_don": f"DH{order_id:04d}" if order_id else None,
        "san_pham_khieu_nai": complaint.san_pham_khieu_nai,
        "tieu_de": complaint.tieu_de,
        "noi_dung": complaint.noi_dung,
        "trang_thai": complaint.trang_thai,
        "ngay_khieu_nai": complaint.ngay_khieu_nai,
    }


def lay_danh_sach_khieu_nai(
    db: Session,
    params: PaginationParams,
    account: TaiKhoan,
    status_filter: str | None = None,
) -> tuple[list[KhieuNai], int]:
    stmt = select(KhieuNai)
    count_stmt = select(func.count()).select_from(KhieuNai)

    if not _xem_toan_bo(account):
        if not account.customer:
            return [], 0
        stmt = stmt.where(KhieuNai.id_khach_hang == account.customer.id_khach_hang)
        count_stmt = count_stmt.where(KhieuNai.id_khach_hang == account.customer.id_khach_hang)
    if status_filter:
        stmt = stmt.where(KhieuNai.trang_thai == status_filter)
        count_stmt = count_stmt.where(KhieuNai.trang_thai == status_filter)

    total = db.scalar(count_stmt) or 0
    complaints = db.scalars(
        stmt.order_by(KhieuNai.ngay_khieu_nai.desc(), KhieuNai.id_khieu_nai.desc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(complaints), total


def lay_khieu_nai_cua_toi(db: Session, account: TaiKhoan) -> list[dict[str, Any]]:
    if not account.customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cần có hồ sơ khách hàng để xem khiếu nại của bạn")

    complaints = db.scalars(
        select(KhieuNai)
        .where(KhieuNai.id_khach_hang == account.customer.id_khach_hang)
        .order_by(KhieuNai.ngay_khieu_nai.desc(), KhieuNai.id_khieu_nai.desc())
    ).all()
    return [khieu_nai_sang_dict_nguoi_dung(complaint) for complaint in complaints]


def lay_danh_sach_khieu_nai_admin(
    db: Session,
    params: PaginationParams,
    account: TaiKhoan,
) -> tuple[list[dict[str, Any]], int]:
    _dam_bao_nhan_vien(account)
    stmt = (
        select(KhieuNai, KhachHang, DonThue)
        .join(KhachHang, KhieuNai.id_khach_hang == KhachHang.id_khach_hang)
        .outerjoin(DonThue, KhieuNai.id_don_thue == DonThue.id_don_thue)
        .order_by(KhieuNai.ngay_khieu_nai.desc(), KhieuNai.id_khieu_nai.desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    count_stmt = select(func.count()).select_from(KhieuNai)

    rows = db.execute(stmt).all()
    total = db.scalar(count_stmt) or 0
    return [khieu_nai_sang_dict_admin(complaint, customer, rental) for complaint, customer, rental in rows], total


def lay_khieu_nai_hoac_404(db: Session, complaint_id: int, account: TaiKhoan) -> KhieuNai:
    complaint = db.get(KhieuNai, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy khiếu nại")
    _dam_bao_quyen_truy_cap(account, complaint)
    return complaint


def tao_khieu_nai(db: Session, payload: KhieuNaiTao, account: TaiKhoan) -> KhieuNai:
    if not account.customer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cần có hồ sơ khách hàng để xem khiếu nại của bạn")

    customer_id = account.customer.id_khach_hang
    rental: DonThue | None = None
    product_names: list[str] = []
    if payload.id_don_thue is not None:
        rental = _lay_don_thue_kem_chi_tiet(db, payload.id_don_thue)
        if rental.id_khach_hang != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không thể khiếu nại đơn hàng của tài khoản khác",
            )
        if not payload.id_thiet_bi_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vui lòng chọn sản phẩm khiếu nại")
        product_names = _danh_sach_ten_thiet_bi_duoc_chon(rental, payload.id_thiet_bi_list)

    complaint = KhieuNai(
        id_don_thue=rental.id_don_thue if rental else None,
        id_khach_hang=customer_id,
        tieu_de=(payload.tieu_de or "Khiếu nại").strip(),
        san_pham_khieu_nai=(
            json.dumps(product_names, ensure_ascii=False)
            if product_names
            else None
        ),
        noi_dung=payload.noi_dung.strip(),
        trang_thai=TRANG_THAI_KHIEU_NAI_MAC_DINH,
        ngay_khieu_nai=datetime.now(),
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def cap_nhat_khieu_nai(
    db: Session,
    complaint_id: int,
    payload: KhieuNaiCapNhat,
    account: TaiKhoan,
) -> KhieuNai:
    _dam_bao_nhan_vien(account)
    complaint = lay_khieu_nai_hoac_404(db, complaint_id, account)
    data = payload.model_dump(exclude_unset=True)

    if "id_don_thue" in data and data["id_don_thue"] is not None:
        rental = _lay_don_thue_kem_chi_tiet(db, data["id_don_thue"])
    else:
        rental = None
    if "id_khach_hang" in data:
        _kiem_tra_ton_tai_khach_hang(db, data["id_khach_hang"])
    effective_customer_id = data.get("id_khach_hang", complaint.id_khach_hang)
    if rental is not None and effective_customer_id is not None and rental.id_khach_hang != effective_customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Khách hàng không khớp với đơn hàng được chọn")
    if "trang_thai" in data and data["trang_thai"]:
        data["trang_thai"] = _kiem_tra_trang_thai(data["trang_thai"])

    for field, value in data.items():
        setattr(complaint, field, value)
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def cap_nhat_trang_thai_khieu_nai(
    db: Session,
    complaint_id: int,
    payload: TrangThaiKhieuNaiCapNhat,
    account: TaiKhoan,
) -> KhieuNai:
    _dam_bao_nhan_vien(account)
    complaint = lay_khieu_nai_hoac_404(db, complaint_id, account)
    complaint.trang_thai = _kiem_tra_trang_thai(payload.trang_thai)
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def xoa_khieu_nai(db: Session, complaint_id: int, account: TaiKhoan) -> None:
    if account.vai_tro != VAI_TRO_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vai trò admin là bắt buộc")
    complaint = lay_khieu_nai_hoac_404(db, complaint_id, account)
    db.delete(complaint)
    db.commit()
