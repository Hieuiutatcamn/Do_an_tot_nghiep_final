from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.tai_khoan import TaiKhoan
from app.schemas.thanh_toan import (
    KetQuaThanhToanVnpayPhanHoi,
    TaoThanhToanVnpayPhanHoi,
    TaoThanhToanVnpayYeuCau,
)
from app.services import thanh_toan_service
from app.utils.dependencies import get_current_account

router = APIRouter(prefix="/thanh-toan", tags=["Thanh toán"])
router_tuong_thich = APIRouter(
    prefix="/thanh_toan",
    tags=["Thanh toán tương thích"],
)


def _dia_chi_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    ip_address = forwarded or (request.client.host if request.client else "127.0.0.1")
    return "127.0.0.1" if ip_address == "::1" else ip_address


@router.post("/vnpay-tao-url", response_model=TaoThanhToanVnpayPhanHoi)
def tao_duong_dan_thanh_toan_vnpay(
    payload: TaoThanhToanVnpayYeuCau,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    duong_dan = thanh_toan_service.tao_duong_dan_thanh_toan_vnpay(
        db,
        payload,
        account,
        _dia_chi_ip(request),
    )
    return {"thanh_cong": True, "duong_dan_thanh_toan": duong_dan}


@router.get("/vnpay-return", response_model=KetQuaThanhToanVnpayPhanHoi)
@router_tuong_thich.get(
    "/vnpay_return",
    response_model=KetQuaThanhToanVnpayPhanHoi,
    include_in_schema=False,
)
def xu_ly_ket_qua_vnpay(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    return thanh_toan_service.xu_ly_ket_qua_vnpay(db, dict(request.query_params))


@router.get("/vnpay-ipn")
@router_tuong_thich.get("/vnpay_ipn", include_in_schema=False)
def xu_ly_ipn_vnpay(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    return thanh_toan_service.xu_ly_ipn_vnpay(db, dict(request.query_params))
