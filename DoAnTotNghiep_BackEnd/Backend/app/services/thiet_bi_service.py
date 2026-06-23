from datetime import date
from decimal import Decimal
import unicodedata

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.danh_muc import DanhMuc
from app.models.hang_so import THIET_BI_SAN_SANG, THIET_BI_DANG_THUE
from app.models.thiet_bi import ThietBi
from app.schemas.thiet_bi import ThietBiTao, ThietBiCapNhat
from app.services import kiem_tra_lich_thue_service
from app.utils.pagination import PaginationParams


def chuan_hoa_trang_thai_thiet_bi(quantity: int | None, status_value: str | None = None) -> str:
    if quantity is not None:
        return THIET_BI_SAN_SANG if quantity > 0 else THIET_BI_DANG_THUE
    return status_value or THIET_BI_DANG_THUE


def _tach_gia_tri_bo_loc(*values: object) -> list[str]:
    result: list[str] = []
    for value in values:
        if value is None:
            continue
        candidates = value if isinstance(value, (list, tuple, set)) else [value]
        for candidate in candidates:
            if candidate is None:
                continue
            for part in str(candidate).split(","):
                item = part.strip()
                if item and item not in result:
                    result.append(item)
    return result


def _normalize_filter_text(value: str | None) -> str:
    text = str(value or "").strip().lower()
    normalized = unicodedata.normalize("NFD", text)
    return "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    ).replace("đ", "d")


def _gia_tri_loc_trang_thai(status_value: object = None, statuses_value: object = None) -> list[str]:
    status_values: list[str] = []
    for raw_status in _tach_gia_tri_bo_loc(status_value, statuses_value):
        normalized_status = _normalize_filter_text(raw_status)
        if "san sang" in normalized_status or normalized_status == "available":
            candidates = [THIET_BI_SAN_SANG, "Sẵn sàng", "San sang"]
        elif "dang thue" in normalized_status or "dang duoc thue" in normalized_status or normalized_status == "rented":
            candidates = [THIET_BI_DANG_THUE, "Đang thuê", "Đang được thuê", "Dang thue", "Dang duoc thue"]
        else:
            candidates = [raw_status]

        for candidate in candidates:
            if candidate and candidate not in status_values:
                status_values.append(candidate)
    return status_values


def _bieu_thuc_sap_xep(sort: str | None):
    sort_key = (sort or "").strip().lower()
    if sort_key == "price_asc":
        return ThietBi.gia_thue.asc()
    if sort_key == "price_desc":
        return ThietBi.gia_thue.desc()
    if sort_key == "name_asc":
        return ThietBi.ten_thiet_bi.asc()
    if sort_key == "name_desc":
        return ThietBi.ten_thiet_bi.desc()
    if sort_key == "newest":
        return ThietBi.id_thiet_bi.desc()
    return ThietBi.id_thiet_bi.asc()


def _truy_van_thiet_bi_da_loc(
    search: str | None = None,
    category_id: int | None = None,
    category: list[str] | None = None,
    categories: str | None = None,
    status_value: list[str] | None = None,
    statuses: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    available_only: bool = False,
):
    stmt = select(ThietBi).options(selectinload(ThietBi.category)).outerjoin(ThietBi.category)
    count_stmt = select(func.count(ThietBi.id_thiet_bi)).select_from(ThietBi).outerjoin(ThietBi.category)

    conditions = []
    if search:
        keyword = f"%{search.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(ThietBi.ten_thiet_bi).like(keyword),
                func.lower(ThietBi.mo_ta).like(keyword),
            )
        )

    category_values = _tach_gia_tri_bo_loc(category, categories)
    category_ids: list[int] = []
    category_names: list[str] = []
    if category_id is not None:
        category_ids.append(category_id)
    for category_value in category_values:
        if category_value.isdigit():
            category_ids.append(int(category_value))
        else:
            category_names.append(category_value)
    if category_ids or category_names:
        category_conditions = []
        if category_ids:
            category_conditions.append(ThietBi.danh_muc_id.in_(category_ids))
        for category_name in category_names:
            category_conditions.append(
                func.lower(DanhMuc.ten_danh_muc).like(f"%{category_name.lower()}%")
            )
        conditions.append(or_(*category_conditions))

    device_statuses = _gia_tri_loc_trang_thai(status_value, statuses)
    if device_statuses:
        conditions.append(ThietBi.tinh_trang.in_(device_statuses))

    if min_price is not None and max_price is not None and max_price < min_price:
        min_price, max_price = max_price, min_price
    if min_price is not None:
        conditions.append(ThietBi.gia_thue >= min_price)
    if max_price is not None:
        conditions.append(ThietBi.gia_thue <= max_price)

    if available_only:
        conditions.append((ThietBi.so_luong.is_not(None)) & (ThietBi.so_luong > 0))

    for condition in conditions:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    return stmt, count_stmt


def lay_danh_sach_thiet_bi(
    db: Session,
    params: PaginationParams,
    search: str | None = None,
    category_id: int | None = None,
    category: list[str] | None = None,
    categories: str | None = None,
    status: list[str] | None = None,
    statuses: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort: str | None = None,
    available_only: bool = False,
) -> tuple[list[ThietBi], int]:
    stmt, count_stmt = _truy_van_thiet_bi_da_loc(
        search=search,
        category_id=category_id,
        category=category,
        categories=categories,
        status_value=status,
        statuses=statuses,
        min_price=min_price,
        max_price=max_price,
        available_only=available_only,
    )
    total = db.scalar(count_stmt) or 0
    devices = db.scalars(
        stmt.order_by(_bieu_thuc_sap_xep(sort))
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(devices), total


def _du_lieu_danh_muc(device: ThietBi) -> dict[str, object] | None:
    if not device.category:
        return None
    return {
        "id_danh_muc": device.category.id_danh_muc,
        "ten_danh_muc": device.category.ten_danh_muc,
        "mo_ta": device.category.mo_ta,
    }


def _du_lieu_thiet_bi_co_the_thue(device: ThietBi, summary: dict[str, object]) -> dict[str, object]:
    available_quantity = int(summary.get("so_luong_kha_dung") or 0)
    return {
        "id_thiet_bi": device.id_thiet_bi,
        "ten_thiet_bi": device.ten_thiet_bi,
        "danh_muc_id": device.danh_muc_id,
        "so_luong": available_quantity,
        "gia_thue": device.gia_thue,
        "tinh_trang": device.tinh_trang,
        "mo_ta": device.mo_ta,
        "hinh_anh": device.hinh_anh,
        "category": _du_lieu_danh_muc(device),
        "tong_so_luong": int(summary.get("tong_so_luong") or 0),
        "so_luong_da_dat": int(summary.get("so_luong_da_dat") or 0),
        "so_luong_kha_dung": available_quantity,
        "available": available_quantity > 0,
    }


def lay_thiet_bi_kha_dung(
    db: Session,
    ngay_nhan: date,
    ngay_tra: date,
    search: str | None = None,
    category_id: int | None = None,
    category: list[str] | None = None,
    categories: str | None = None,
    status: list[str] | None = None,
    statuses: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort: str | None = None,
) -> list[dict[str, object]]:
    kiem_tra_lich_thue_service.chuan_hoa_khoang_thue(ngay_nhan, ngay_tra)
    stmt, _ = _truy_van_thiet_bi_da_loc(
        search=search,
        category_id=category_id,
        category=category,
        categories=categories,
        status_value=status,
        statuses=statuses,
        min_price=min_price,
        max_price=max_price,
        available_only=False,
    )
    devices = db.scalars(stmt.order_by(_bieu_thuc_sap_xep(sort))).all()
    available_devices: list[dict[str, object]] = []
    for device in devices:
        summary = kiem_tra_lich_thue_service.tom_tat_kha_dung(
            db,
            device.id_thiet_bi,
            ngay_nhan,
            ngay_tra,
            device=device,
        )
        if int(summary.get("so_luong_kha_dung") or 0) > 0:
            available_devices.append(_du_lieu_thiet_bi_co_the_thue(device, summary))
    return available_devices


def tim_kiem_thiet_bi_theo_id(db: Session, id_thiet_bi: int) -> ThietBi:
    device = db.scalar(
        select(ThietBi)
        .options(selectinload(ThietBi.category))
        .where(ThietBi.id_thiet_bi == id_thiet_bi)
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thiết bị")
    return device


def tao_thiet_bi(db: Session, payload: ThietBiTao) -> ThietBi:
    data = payload.model_dump()
    data["tinh_trang"] = data.get("tinh_trang") or chuan_hoa_trang_thai_thiet_bi(data.get("so_luong"))
    device = ThietBi(**data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return tim_kiem_thiet_bi_theo_id(db, device.id_thiet_bi)


def cap_nhat_thiet_bi(db: Session, id_thiet_bi: int, payload: ThietBiCapNhat) -> ThietBi:
    device = tim_kiem_thiet_bi_theo_id(db, id_thiet_bi)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(device, field, value)
    if "so_luong" in data and "tinh_trang" not in data:
        device.tinh_trang = chuan_hoa_trang_thai_thiet_bi(device.so_luong)
    db.add(device)
    db.commit()
    db.refresh(device)
    return tim_kiem_thiet_bi_theo_id(db, device.id_thiet_bi)


def cap_nhat_anh_thiet_bi(db: Session, id_thiet_bi: int, image_path: str) -> ThietBi:
    device = tim_kiem_thiet_bi_theo_id(db, id_thiet_bi)
    device.hinh_anh = image_path
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def xoa_thiet_bi(db: Session, id_thiet_bi: int) -> None:
    device = tim_kiem_thiet_bi_theo_id(db, id_thiet_bi)
    db.delete(device)
    db.commit()
