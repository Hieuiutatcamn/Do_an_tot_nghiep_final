from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN
from app.models.nhan_vien import NhanVien
from app.schemas.nhan_vien import NhanVienTao, NhanVienCapNhat
from app.utils.pagination import PaginationParams


def lay_danh_sach_nhan_vien(db: Session, params: PaginationParams) -> tuple[list[NhanVien], int]:
    total = db.scalar(select(func.count()).select_from(NhanVien)) or 0
    employees = db.scalars(
        select(NhanVien)
        .options(selectinload(NhanVien.account))
        .order_by(NhanVien.id_nhan_vien.asc())
        .offset(params.offset)
        .limit(params.page_size)
    ).all()
    return list(employees), total


def lay_nhan_vien_hoac_404(db: Session, employee_id: int) -> NhanVien:
    employee = db.scalar(
        select(NhanVien)
        .options(selectinload(NhanVien.account))
        .where(NhanVien.id_nhan_vien == employee_id)
    )
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhân viên")
    return employee


def _kiem_tra_lien_ket_tai_khoan(
    db: Session,
    account_id: int | None,
    ignore_employee_id: int | None = None,
) -> None:
    if account_id is None:
        return
    account = db.get(TaiKhoan, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản không tồn tại")
    if account.vai_tro and account.vai_tro not in {VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vai trò tài khoản phải là Admin hoặc Nhân viên",
        )

    stmt = select(NhanVien).where(NhanVien.id_tai_khoan == account_id)
    if ignore_employee_id is not None:
        stmt = stmt.where(NhanVien.id_nhan_vien != ignore_employee_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tài khoản đã được liên kết với một nhân viên khác")


def tao_nhan_vien(db: Session, payload: NhanVienTao) -> NhanVien:
    _kiem_tra_lien_ket_tai_khoan(db, payload.id_tai_khoan)
    employee = NhanVien(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return lay_nhan_vien_hoac_404(db, employee.id_nhan_vien)


def cap_nhat_nhan_vien(db: Session, employee_id: int, payload: NhanVienCapNhat) -> NhanVien:
    employee = lay_nhan_vien_hoac_404(db, employee_id)
    data = payload.model_dump(exclude_unset=True)
    if "id_tai_khoan" in data:
        _kiem_tra_lien_ket_tai_khoan(db, data["id_tai_khoan"], ignore_employee_id=employee_id)
    for field, value in data.items():
        setattr(employee, field, value)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return lay_nhan_vien_hoac_404(db, employee.id_nhan_vien)


def xoa_nhan_vien(db: Session, employee_id: int) -> None:
    employee = lay_nhan_vien_hoac_404(db, employee_id)
    db.delete(employee)
    db.commit()
