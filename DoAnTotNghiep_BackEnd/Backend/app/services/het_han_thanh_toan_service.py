import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.don_thue import DonThue
from app.services import thong_bao_service

logger = logging.getLogger(__name__)

TRANG_THAI_CHO_THANH_TOAN = "Cho thanh toan"
TRANG_THAI_DA_HUY = "Da huy"
GHI_CHU_TU_DONG_HUY_VNPAY = (
    "Hệ thống tự động hủy do quá thời gian thanh toán VNPAY."
)


def thoi_gian_hien_tai() -> datetime:
    return datetime.now()


def la_don_tu_dong_huy_do_het_han_vnpay(don_thue: DonThue) -> bool:
    return GHI_CHU_TU_DONG_HUY_VNPAY in str(don_thue.ghi_chu or "")


def _them_ghi_chu_tu_dong_huy(don_thue: DonThue) -> None:
    ghi_chu_hien_tai = str(don_thue.ghi_chu or "").strip()
    if GHI_CHU_TU_DONG_HUY_VNPAY in ghi_chu_hien_tai:
        return
    don_thue.ghi_chu = (
        f"{ghi_chu_hien_tai}\n{GHI_CHU_TU_DONG_HUY_VNPAY}".strip()[:255]
    )


def bo_ghi_chu_tu_dong_huy_vnpay(don_thue: DonThue) -> None:
    cac_dong = [
        dong.strip()
        for dong in str(don_thue.ghi_chu or "").splitlines()
        if dong.strip() and dong.strip() != GHI_CHU_TU_DONG_HUY_VNPAY
    ]
    don_thue.ghi_chu = "\n".join(cac_dong)[:255] or None


def huy_cac_don_vnpay_het_han(
    db: Session,
    *,
    tai_thoi_diem: datetime | None = None,
    commit: bool = True,
) -> int:
    hien_tai = tai_thoi_diem or thoi_gian_hien_tai()
    cac_don_het_han = db.scalars(
        select(DonThue)
        .where(
            DonThue.trang_thai == TRANG_THAI_CHO_THANH_TOAN,
            DonThue.phuong_thuc_thanh_toan == "VNPAY",
            DonThue.han_thanh_toan_vnpay.is_not(None),
            DonThue.han_thanh_toan_vnpay <= hien_tai,
            DonThue.ma_giao_dich_vnpay.is_(None),
        )
        .with_for_update()
    ).all()

    for don_thue in cac_don_het_han:
        don_thue.trang_thai = TRANG_THAI_DA_HUY
        _them_ghi_chu_tu_dong_huy(don_thue)
        db.add(don_thue)
        thong_bao_service.them_thong_bao_het_han_thanh_toan_vnpay(
            db,
            don_thue,
        )

    if cac_don_het_han and commit:
        db.commit()
        logger.info(
            "Đã tự động hủy %s đơn VNPAY hết hạn thanh toán.",
            len(cac_don_het_han),
        )
    elif cac_don_het_han:
        db.flush()
    return len(cac_don_het_han)
