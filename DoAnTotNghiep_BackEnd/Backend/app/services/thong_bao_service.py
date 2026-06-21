from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import TAI_KHOAN_HOAT_DONG, VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN
from app.models.khach_hang import KhachHang
from app.models.thong_bao import ThongBao
from app.models.don_thue import DonThue
from app.schemas.thong_bao import ThongBaoTao

NOI_DUNG_THONG_BAO_TRANG_THAI_DON_THUE = {
    "Da xac nhan": (
        "Xác nhận đơn thuê",
        "Đơn thuê #{rental_id} đã được xác nhận.",
    ),
    "Da qua han": (
        "Đơn thuê quá hạn",
        "Đơn thuê #{rental_id} đã quá hạn.",
    ),
    "Da thue": (
        "Đơn thuê hoàn tất",
        "Đơn thuê #{rental_id} đã hoàn tất.",
    ),
}


def _tim_nguoi_nhan_theo_tai_khoan(account: TaiKhoan) -> str:
    if account.vai_tro == VAI_TRO_ADMIN:
        return "Admin"
    if account.vai_tro == VAI_TRO_NHAN_VIEN:
        return "Nhan vien"
    return "User"


def _bo_loc_hien_thi(account: TaiKhoan):
    return or_(
        ThongBao.id_tai_khoan == account.id_tai_khoan,
        (
            (ThongBao.id_tai_khoan.is_(None))
            & (ThongBao.doi_tuong_nhan == _tim_nguoi_nhan_theo_tai_khoan(account))
        ),
    )


def _lay_thong_bao_co_quyen_truy_cap(db: Session, notification_id: int, account: TaiKhoan) -> ThongBao:
    notification = db.scalar(
        select(ThongBao)
        .options(selectinload(ThongBao.rental).selectinload(DonThue.customer))
        .where(
            ThongBao.id_thong_bao == notification_id,
            _bo_loc_hien_thi(account),
        )
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông báo")
    gan_thong_tin_bo_sung(notification)
    return notification


def gan_thong_tin_bo_sung(notification: ThongBao) -> ThongBao:
    rental = getattr(notification, "rental", None)
    customer = getattr(rental, "customer", None) if rental else None
    notification.ten_khach_hang = customer.ho_ten if customer else None
    return notification


def lay_danh_sach_thong_bao(
    db: Session,
    account: TaiKhoan,
    status_filter: str | None = None,
) -> list[ThongBao]:
    stmt = (
        select(ThongBao)
        .options(selectinload(ThongBao.rental).selectinload(DonThue.customer))
        .where(_bo_loc_hien_thi(account))
    )
    if status_filter:
        stmt = stmt.where(ThongBao.trang_thai == status_filter)
    items = db.scalars(stmt.order_by(ThongBao.ngay_tao.desc(), ThongBao.id_thong_bao.desc())).all()
    return [gan_thong_tin_bo_sung(item) for item in items]


def dem_thong_bao_chua_doc(db: Session, account: TaiKhoan) -> int:
    return db.scalar(
        select(func.count())
        .select_from(ThongBao)
        .where(
            _bo_loc_hien_thi(account),
            ThongBao.trang_thai == "Chua doc",
        )
    ) or 0


def danh_dau_da_doc(db: Session, notification_id: int, account: TaiKhoan) -> ThongBao:
    notification = _lay_thong_bao_co_quyen_truy_cap(db, notification_id, account)
    notification.trang_thai = "Da doc"
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def danh_dau_tat_ca_da_doc(db: Session, account: TaiKhoan) -> int:
    result = db.execute(
        update(ThongBao)
        .where(
            _bo_loc_hien_thi(account),
            ThongBao.trang_thai == "Chua doc",
        )
        .values(trang_thai="Da doc")
    )
    db.commit()
    return result.rowcount or 0


def tao_thong_bao(db: Session, payload: ThongBaoTao, commit: bool = True) -> ThongBao:
    if payload.id_tai_khoan is not None and not db.get(TaiKhoan, payload.id_tai_khoan):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản không tồn tại")
    if payload.id_don_thue is not None and not db.get(DonThue, payload.id_don_thue):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đơn thuê không tồn tại")

    notification = ThongBao(**payload.model_dump())
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    return notification


def xoa_thong_bao(db: Session, notification_id: int, account: TaiKhoan) -> None:
    notification = db.get(ThongBao, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông báo")
    if account.vai_tro != VAI_TRO_ADMIN and notification.id_tai_khoan != account.id_tai_khoan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không thể xóa thông báo này")

    db.delete(notification)
    db.commit()


def _add_customer_notification(
    db: Session,
    rental: DonThue,
    title: str,
    content: str,
    notification_type: str,
) -> None:
    customer = db.get(KhachHang, rental.id_khach_hang) if rental.id_khach_hang else None
    if not customer or not customer.id_tai_khoan:
        return

    db.add(
        ThongBao(
            id_tai_khoan=customer.id_tai_khoan,
            id_don_thue=rental.id_don_thue,
            tieu_de=title,
            noi_dung=content,
            loai_thong_bao=notification_type,
            doi_tuong_nhan="User",
        )
    )


def them_thong_bao_tao_don(db: Session, rental: DonThue) -> None:
    _add_customer_notification(
        db,
        rental,
        "Đặt hàng thành công",
        f"Đơn thuê #{rental.id_don_thue} đã được tạo thành công.",
        "Dat hang thanh cong",
    )

    staff_accounts = db.scalars(
        select(TaiKhoan).where(
            TaiKhoan.vai_tro.in_([VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN]),
            TaiKhoan.trang_thai == TAI_KHOAN_HOAT_DONG,
        )
    ).all()
    for staff_account in staff_accounts:
        db.add(
            ThongBao(
                id_tai_khoan=staff_account.id_tai_khoan,
                id_don_thue=rental.id_don_thue,
                tieu_de="Có đơn hàng mới",
                noi_dung=f"Đơn thuê #{rental.id_don_thue} vừa được tạo.",
                loai_thong_bao="Co don hang moi",
                doi_tuong_nhan="Admin" if staff_account.vai_tro == VAI_TRO_ADMIN else "Nhan vien",
            )
        )


def them_thong_bao_huy_don(db: Session, rental: DonThue) -> None:
    order_id = rental.id_don_thue
    _add_customer_notification(
        db,
        rental,
        "Hủy đơn hàng thành công",
        f"Bạn đã hủy đơn hàng #{order_id} thành công.",
        "Cap nhat don hang",
    )

    staff_accounts = db.scalars(
        select(TaiKhoan).where(
            TaiKhoan.vai_tro.in_([VAI_TRO_ADMIN, VAI_TRO_NHAN_VIEN]),
            TaiKhoan.trang_thai == TAI_KHOAN_HOAT_DONG,
        )
    ).all()
    for staff_account in staff_accounts:
        db.add(
            ThongBao(
                id_tai_khoan=staff_account.id_tai_khoan,
                id_don_thue=rental.id_don_thue,
                tieu_de="Khách hàng hủy đơn hàng",
                noi_dung=f"Khách hàng đã hủy đơn hàng #{order_id}.",
                loai_thong_bao="Cap nhat don hang",
                doi_tuong_nhan="Admin" if staff_account.vai_tro == VAI_TRO_ADMIN else "Nhan vien",
            )
        )


def them_thong_bao_het_han_thanh_toan_vnpay(db: Session, rental: DonThue) -> None:
    _add_customer_notification(
        db,
        rental,
        "Đơn VNPAY đã hết thời gian thanh toán",
        (
            f"Đơn thuê #{rental.id_don_thue} đã tự động hủy vì quá "
            "15 phút thanh toán VNPAY."
        ),
        "Cap nhat don hang",
    )


def them_thong_bao_trang_thai_don(db: Session, rental: DonThue) -> None:
    content = NOI_DUNG_THONG_BAO_TRANG_THAI_DON_THUE.get(rental.trang_thai or "")
    if not content:
        return

    title, message_template = content
    _add_customer_notification(
        db,
        rental,
        title,
        message_template.format(rental_id=rental.id_don_thue),
        "Cap nhat don hang",
    )
