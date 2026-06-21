from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile
from starlette.responses import RedirectResponse

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.xac_thuc import (
    TaiKhoanPhanHoi,
    HoSoKhachHangPhanHoi,
    DangNhapYeuCau,
    DoiMatKhauPhanHoi,
    DoiMatKhauYeuCau,
    ToiPhanHoi,
    LamMoiTokenYeuCau,
    DangKyYeuCau,
    TokenPhanHoi,
)
from app.services.xac_thuc_service import (
    _lay_thong_bao_co_quyen_truy_cap,
    doi_mat_khau,
    tao_phan_hoi_token,
    dang_ky_khach_hang,
    kiem_tra_dang_ky_khong_trung,
)
from app.services import dang_nhap_xa_hoi_service
from app.utils.config import get_settings
from app.utils.dependencies import get_current_account
from app.utils.security import decode_token
from app.utils.upload import delete_upload_file, save_upload_file

router = APIRouter(prefix="/xac-thuc", tags=["Xác thực"])

REGISTER_FIELDS = (
    "username",
    "password",
    "ho_ten",
    "sdt",
    "cccd",
    "email",
    "so_cccd",
    "anh_cccd_mat_truoc",
    "anh_cccd_mat_sau",
    "anh_cccd",
)


async def parse_register_request(request: Request) -> tuple[DangKyYeuCau, UploadFile | None, UploadFile | None]:
    content_type = request.headers.get("content-type", "").lower()
    front_file: UploadFile | None = None
    back_file: UploadFile | None = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        data = {field: form.get(field) for field in REGISTER_FIELDS if form.get(field) not in (None, "")}
        front_value = form.get("cccd_truoc")
        back_value = form.get("cccd_sau")
        front_file = front_value if isinstance(front_value, UploadFile) else None
        back_file = back_value if isinstance(back_value, UploadFile) else None
        if not front_file or not back_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vui lòng chọn đầy đủ ảnh CCCD mặt trước và mặt sau",
            )
    else:
        try:
            data = await request.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dữ liệu đăng ký không hợp lệ",
            ) from exc

    try:
        return DangKyYeuCau.model_validate(data), front_file, back_file
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def oauth_frontend_redirect(**params: str) -> RedirectResponse:
    fragment = urlencode({key: value for key, value in params.items() if value})
    frontend_login_url = get_settings().oauth_frontend_login_url_value()
    response = RedirectResponse(f"{frontend_login_url}#{fragment}", status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def oauth_error_redirect(nha_cung_cap: str, message: str | None = None) -> RedirectResponse:
    return oauth_frontend_redirect(
        oauth_error=message or f"Đăng nhập {dang_nhap_xa_hoi_service.nhan_nha_cung_cap(nha_cung_cap)} thất bại.",
        nha_cung_cap=nha_cung_cap,
    )


def facebook_success_redirect(tokens: TokenPhanHoi) -> RedirectResponse:
    query = urlencode(
        {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
        }
    )
    return RedirectResponse(
        f"{get_settings().facebook_frontend_success_url}?{query}",
        status_code=status.HTTP_302_FOUND,
    )


def oauth_login_redirect(nha_cung_cap: str) -> RedirectResponse:
    try:
        return RedirectResponse(dang_nhap_xa_hoi_service.tao_url_uy_quyen(nha_cung_cap), status_code=status.HTTP_302_FOUND)
    except HTTPException as exc:
        return oauth_error_redirect(nha_cung_cap, str(exc.detail))


async def oauth_callback_redirect(
    nha_cung_cap: str,
    db: Session,
    code: str | None,
    state_token: str | None,
    nha_cung_cap_error: str | None,
) -> RedirectResponse:
    if nha_cung_cap_error or not code or not state_token:
        return oauth_error_redirect(nha_cung_cap)
    try:
        dang_nhap_xa_hoi_service.kiem_tra_trang_thai_oauth(nha_cung_cap, state_token)
        profile = await dang_nhap_xa_hoi_service.doi_ma_lay_ho_so(nha_cung_cap, code)
        tokens = dang_nhap_xa_hoi_service.dang_nhap_hoac_tao_khach_hang_oauth(db, profile)
        if nha_cung_cap == "facebook":
            return facebook_success_redirect(tokens)
        return oauth_frontend_redirect(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            nha_cung_cap=nha_cung_cap,
        )
    except HTTPException as exc:
        return oauth_error_redirect(nha_cung_cap, str(exc.detail))
    except Exception:
        return oauth_error_redirect(nha_cung_cap)


@router.post("/register", response_model=TokenPhanHoi, status_code=status.HTTP_201_CREATED)
async def register(request: Request, db: Annotated[Session, Depends(get_db)]) -> TokenPhanHoi:
    payload, front_file, back_file = await parse_register_request(request)
    if front_file and back_file:
        kiem_tra_dang_ky_khong_trung(db, payload)
        saved_paths: list[str] = []
        try:
            front_path = await save_upload_file(front_file, "cccd")
            saved_paths.append(front_path)
            back_path = await save_upload_file(back_file, "cccd")
            saved_paths.append(back_path)
            payload = payload.model_copy(
                update={
                    "anh_cccd_mat_truoc": front_path,
                    "anh_cccd_mat_sau": back_path,
                }
            )
            return dang_ky_khach_hang(db, payload)
        except Exception:
            for saved_path in saved_paths:
                delete_upload_file(saved_path)
            raise
        finally:
            await front_file.close()
            await back_file.close()
    return dang_ky_khach_hang(db, payload)


@router.get("/google/login")
def dang_nhap_google() -> RedirectResponse:
    return oauth_login_redirect("google")


@router.get("/google/callback")
async def xu_ly_callback_google(
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    return await oauth_callback_redirect("google", db, code, state, error)


@router.get("/facebook/login")
def facebook_login() -> RedirectResponse:
    return oauth_login_redirect("facebook")


@router.get("/facebook/callback")
async def facebook_callback(
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    return await oauth_callback_redirect("facebook", db, code, state, error)


@router.post("/login", response_model=TokenPhanHoi)
def login(payload: DangNhapYeuCau, db: Annotated[Session, Depends(get_db)]) -> TokenPhanHoi:
    return _lay_thong_bao_co_quyen_truy_cap(db, payload)


@router.post("/token", response_model=TokenPhanHoi)
def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenPhanHoi:
    payload = DangNhapYeuCau(username=form_data.username, password=form_data.password)
    return _lay_thong_bao_co_quyen_truy_cap(db, payload)


@router.post("/refresh", response_model=TokenPhanHoi)
def refresh_token(
    payload: LamMoiTokenYeuCau,
    db: Annotated[Session, Depends(get_db)],
) -> TokenPhanHoi:
    try:
        token_payload = decode_token(payload.refresh_token, "refresh")
        account_id = int(token_payload.get("sub", "0"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    account = db.get(TaiKhoan, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return tao_phan_hoi_token(account.id_tai_khoan)


@router.get("/me", response_model=ToiPhanHoi)
def me(account: Annotated[TaiKhoan, Depends(get_current_account)]) -> ToiPhanHoi:
    customer = HoSoKhachHangPhanHoi.model_validate(account.customer) if account.customer else None
    return ToiPhanHoi(
        account=TaiKhoanPhanHoi.model_validate(account),
        customer=customer,
        id=account.id_tai_khoan,
        ho_ten=customer.ho_ten if customer else None,
        email=customer.email if customer else None,
        anh_dai_dien=account.anh_dai_dien,
        nha_cung_cap=account.nha_cung_cap or "local",
    )


@router.put("/change-password", response_model=DoiMatKhauPhanHoi)
def change_password(
    payload: DoiMatKhauYeuCau,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> DoiMatKhauPhanHoi:
    doi_mat_khau(db, account, payload)
    return DoiMatKhauPhanHoi(message="Đổi mật khẩu thành công")


legacy_router = tao_router_ke_thua(router, "/auth", tags=["Xác thực legacy"])
