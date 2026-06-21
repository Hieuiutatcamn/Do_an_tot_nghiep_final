from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.danh_muc import DanhMuc
from app.schemas.danh_muc import DanhMucTao, DanhMucCapNhat
from app.utils.pagination import PaginationParams


def lay_danh_sach_danh_muc(db: Session, params: PaginationParams) -> tuple[list[DanhMuc], int]:
    tong_so_danh_muc = db.scalar(select(func.count()).select_from(DanhMuc)) or 0
    danh_muc = db.scalars(
        select(DanhMuc)
        .order_by(DanhMuc.id_danh_muc.asc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(danh_muc), tong_so_danh_muc


def lay_danh_muc_hoac_404(db: Session, category_id: int) -> DanhMuc:
    danh_muc = db.get(DanhMuc, category_id)
    if not danh_muc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy danh mục")
    return danh_muc


def tao_danh_muc(db: Session, payload: DanhMucTao) -> DanhMuc:
    danh_muc = DanhMuc(**payload.model_dump())
    db.add(danh_muc)
    db.commit()
    db.refresh(danh_muc)
    return danh_muc


def cap_nhat_danh_muc(db: Session, category_id: int, payload: DanhMucCapNhat) -> DanhMuc:
    danh_muc = lay_danh_muc_hoac_404(db, category_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(danh_muc, field, value)
    db.add(danh_muc)
    db.commit()
    db.refresh(danh_muc)
    return danh_muc


def xoa_danh_muc(db: Session, category_id: int) -> None:
    danh_muc = lay_danh_muc_hoac_404(db, category_id)
    db.delete(danh_muc)
    db.commit()
