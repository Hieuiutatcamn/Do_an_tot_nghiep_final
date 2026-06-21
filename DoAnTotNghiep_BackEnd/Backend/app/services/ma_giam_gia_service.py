from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN
from app.models.ma_giam_gia import MaGiamGia
from app.schemas.ma_giam_gia import (
    ApDungMaGiamGiaYeuCau,
    ApDungMaGiamGiaPhanHoi,
    MaGiamGiaTao,
    TrangThaiMaGiamGiaCapNhat,
    MaGiamGiaCapNhat,
)
from app.utils.pagination import PaginationParams

TRANG_THAI_DANG_HOAT_DONG = "dang_hoat_dong"


def _yeu_cau_quyen_xem_admin_hoac_nhan_vien(account: TaiKhoan) -> None:
    if account.vai_tro not in {VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này.",
        )


def _yeu_cau_quyen_quan_tri(account: TaiKhoan) -> None:
    if account.vai_tro != VAI_TRO_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này.",
        )


def _money(value: Decimal | int | float | str | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _hom_nay() -> date:
    return date.today()


def _chuan_hoa_ma(value: str | None) -> str:
    return str(value or "").strip().upper()


def _so_lan_su_dung_con_lai(discount: MaGiamGia) -> bool:
    quantity = int(discount.so_luong or 0)
    used = int(discount.da_su_dung or 0)
    return quantity <= 0 or used < quantity


def _so_tien_giam(discount: MaGiamGia, total: Decimal) -> Decimal:
    value = _money(discount.gia_tri_giam)
    if discount.loai_giam_gia == "phan_tram":
        return _money(total * value / Decimal("100"))
    return min(value, total)


def _danh_gia_dieu_kien(discount: MaGiamGia | None, total: Decimal, days: int) -> ApDungMaGiamGiaPhanHoi:
    if not discount:
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message="Mã giảm giá không tồn tại",
            tong_tien_sau_giam=total,
        )

    today = _hom_nay()
    if discount.trang_thai != TRANG_THAI_DANG_HOAT_DONG:
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message="Mã giảm giá hiện không hoạt động",
            ma_code=discount.ma_code,
            tong_tien_sau_giam=total,
        )
    if discount.ngay_bat_dau and today < discount.ngay_bat_dau:
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message="Mã giảm giá chưa đến thời gian áp dụng",
            ma_code=discount.ma_code,
            tong_tien_sau_giam=total,
        )
    if discount.ngay_ket_thuc and today > discount.ngay_ket_thuc:
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message="Mã giảm giá đã hết hạn",
            ma_code=discount.ma_code,
            tong_tien_sau_giam=total,
        )
    if not _so_lan_su_dung_con_lai(discount):
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message="Mã giảm giá đã hết lượt sử dụng",
            ma_code=discount.ma_code,
            tong_tien_sau_giam=total,
        )

    condition = discount.dieu_kien_loai or "khong_dieu_kien"
    if condition == "so_ngay_thue" and days < int(discount.so_ngay_thue_toi_thieu or 0):
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message=f"Mã giảm giá chỉ áp dụng khi thuê từ {discount.so_ngay_thue_toi_thieu or 0} ngày trở lên",
            ma_code=discount.ma_code,
            tong_tien_sau_giam=total,
        )
    if condition == "tong_tien_don" and total < _money(discount.gia_tri_don_toi_thieu):
        return ApDungMaGiamGiaPhanHoi(
            valid=False,
            message=f"Mã giảm giá chỉ áp dụng cho đơn từ {int(discount.gia_tri_don_toi_thieu or 0):,}đ",
            ma_code=discount.ma_code,
            tong_tien_sau_giam=total,
        )

    discount_money = _so_tien_giam(discount, total)
    return ApDungMaGiamGiaPhanHoi(
        valid=True,
        message="Áp dụng mã giảm giá thành công",
        id_ma_giam_gia=discount.id_ma_giam_gia,
        ma_code=discount.ma_code,
        loai_giam_gia=discount.loai_giam_gia,
        gia_tri_giam=discount.gia_tri_giam,
        so_tien_giam=discount_money,
        tong_tien_sau_giam=max(Decimal("0"), total - discount_money),
    )


def lay_ma_giam_gia_theo_ma(db: Session, code: str, for_update: bool = False) -> MaGiamGia | None:
    stmt = select(MaGiamGia).where(MaGiamGia.ma_code == _chuan_hoa_ma(code))
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def lay_ma_giam_gia_hoac_404(db: Session, discount_id: int) -> MaGiamGia:
    discount = db.get(MaGiamGia, discount_id)
    if not discount:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy mã giảm giá")
    return discount


def ap_dung_ma_giam_gia(db: Session, payload: ApDungMaGiamGiaYeuCau) -> ApDungMaGiamGiaPhanHoi:
    discount = lay_ma_giam_gia_theo_ma(db, payload.ma_code)
    return _danh_gia_dieu_kien(discount, _money(payload.tong_tien), int(payload.so_ngay_thue or 0))


def xac_thuc_ma_giam_gia_cho_don(
    db: Session,
    total: Decimal,
    days: int,
    ma_code: str | None = None,
    discount_id: int | None = None,
) -> tuple[MaGiamGia | None, Decimal]:
    if not ma_code and not discount_id:
        return None, Decimal("0")

    if discount_id:
        stmt = select(MaGiamGia).where(MaGiamGia.id_ma_giam_gia == discount_id).with_for_update()
        discount = db.scalar(stmt)
    else:
        discount = lay_ma_giam_gia_theo_ma(db, ma_code or "", for_update=True)

    result = _danh_gia_dieu_kien(discount, _money(total), days)
    if not result.valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)
    return discount, _money(result.so_tien_giam)


def danh_dau_ma_giam_gia_da_dung(discount: MaGiamGia | None) -> None:
    if not discount:
        return
    discount.da_su_dung = int(discount.da_su_dung or 0) + 1


def lay_ma_giam_gia_dang_hoat_dong(db: Session) -> list[MaGiamGia]:
    today = _hom_nay()
    items = db.scalars(
        select(MaGiamGia)
        .where(MaGiamGia.trang_thai == TRANG_THAI_DANG_HOAT_DONG)
        .where(or_(MaGiamGia.ngay_bat_dau.is_(None), MaGiamGia.ngay_bat_dau <= today))
        .where(or_(MaGiamGia.ngay_ket_thuc.is_(None), MaGiamGia.ngay_ket_thuc >= today))
        .order_by(MaGiamGia.id_ma_giam_gia.desc())
    ).all()
    return [item for item in items if _so_lan_su_dung_con_lai(item)]


def lay_danh_sach_ma_giam_gia_admin(
    db: Session,
    params: PaginationParams,
    account: TaiKhoan,
    search: str | None = None,
    trang_thai: str | None = None,
    loai_giam_gia: str | None = None,
) -> tuple[list[MaGiamGia], int]:
    _yeu_cau_quyen_xem_admin_hoac_nhan_vien(account)
    stmt = select(MaGiamGia)
    count_stmt = select(func.count()).select_from(MaGiamGia)
    filters = []

    if search and search.strip():
        like = f"%{search.strip()}%"
        filters.append(or_(MaGiamGia.ma_code.ilike(like), MaGiamGia.ten_ma.ilike(like)))
    if trang_thai:
        filters.append(MaGiamGia.trang_thai == trang_thai)
    if loai_giam_gia:
        filters.append(MaGiamGia.loai_giam_gia == loai_giam_gia)

    for item in filters:
        stmt = stmt.where(item)
        count_stmt = count_stmt.where(item)

    total = db.scalar(count_stmt) or 0
    items = db.scalars(
        stmt.order_by(MaGiamGia.id_ma_giam_gia.desc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(items), total


def tao_ma_giam_gia(db: Session, payload: MaGiamGiaTao, account: TaiKhoan) -> MaGiamGia:
    _yeu_cau_quyen_quan_tri(account)
    discount = MaGiamGia(**payload.model_dump())
    db.add(discount)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã giảm giá đã tồn tại") from exc
    db.refresh(discount)
    return discount


def cap_nhat_ma_giam_gia(db: Session, discount_id: int, payload: MaGiamGiaCapNhat, account: TaiKhoan) -> MaGiamGia:
    _yeu_cau_quyen_quan_tri(account)
    discount = lay_ma_giam_gia_hoac_404(db, discount_id)
    data = payload.model_dump(exclude_unset=True)
    if "ma_code" in data:
        data["ma_code"] = _chuan_hoa_ma(data["ma_code"])
    for field, value in data.items():
        setattr(discount, field, value)
    db.add(discount)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã giảm giá đã tồn tại") from exc
    db.refresh(discount)
    return discount


def cap_nhat_trang_thai_ma_giam_gia(
    db: Session,
    discount_id: int,
    payload: TrangThaiMaGiamGiaCapNhat,
    account: TaiKhoan,
) -> MaGiamGia:
    _yeu_cau_quyen_quan_tri(account)
    discount = lay_ma_giam_gia_hoac_404(db, discount_id)
    discount.trang_thai = payload.trang_thai
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


def xoa_ma_giam_gia(db: Session, discount_id: int, account: TaiKhoan) -> None:
    _yeu_cau_quyen_quan_tri(account)
    discount = lay_ma_giam_gia_hoac_404(db, discount_id)
    db.delete(discount)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xóa mã giảm giá đã được sử dụng trong đơn thuê",
        ) from exc
