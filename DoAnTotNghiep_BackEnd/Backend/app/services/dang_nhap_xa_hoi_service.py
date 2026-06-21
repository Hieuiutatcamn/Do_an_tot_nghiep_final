import logging
from dataclasses import dataclass
from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tai_khoan import TaiKhoan
from app.models.hang_so import TAI_KHOAN_HOAT_DONG, VAI_TRO_KHACH_HANG
from app.models.khach_hang import KhachHang
from app.schemas.xac_thuc import TokenPhanHoi
from app.services.xac_thuc_service import tao_phan_hoi_token
from app.utils.config import get_settings
from app.utils.security import create_oauth_state, decode_token, hash_password


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OAuthProfile:
    nha_cung_cap: str
    nha_cung_cap_id: str
    email: str
    ho_ten: str
    anh_dai_dien: str | None = None


def nhan_nha_cung_cap(nha_cung_cap: str) -> str:
    return "Google" if nha_cung_cap == "google" else "Facebook"


def cau_hinh_nha_cung_cap(nha_cung_cap: str) -> dict[str, str]:
    settings = get_settings()
    if nha_cung_cap == "google":
        config = {
            "client_id": settings.google_client_id or "",
            "client_secret": settings.google_client_secret or "",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile",
            "redirect_uri": settings.oauth_callback_url(nha_cung_cap),
        }
    elif nha_cung_cap == "facebook":
        graph_url = f"https://graph.facebook.com/{settings.facebook_api_version}"
        config = {
            "client_id": settings.facebook_client_id or "",
            "client_secret": settings.facebook_client_secret or "",
            "authorize_url": f"https://www.facebook.com/{settings.facebook_api_version}/dialog/oauth",
            "token_url": f"{graph_url}/oauth/access_token",
            "userinfo_url": "https://graph.facebook.com/me",
            "scope": "public_profile,email",
            "redirect_uri": settings.oauth_callback_url(nha_cung_cap),
        }
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth nha_cung_cap không hợp lệ")

    if not config["client_id"] or not config["client_secret"] or not config["redirect_uri"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Đăng nhập {nhan_nha_cung_cap(nha_cung_cap)} chưa được cấu hình.",
        )
    return config


def tao_url_uy_quyen(nha_cung_cap: str) -> str:
    config = cau_hinh_nha_cung_cap(nha_cung_cap)
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": config["scope"],
        "state": create_oauth_state(nha_cung_cap),
    }
    if nha_cung_cap == "google":
        params["prompt"] = "select_account"
    oauth_url = f"{config['authorize_url']}?{urlencode(params)}"
    if nha_cung_cap == "facebook":
        logger.info("FACEBOOK_REDIRECT_URI đang dùng: %s", config["redirect_uri"])
        logger.info("Facebook OAuth URL trước khi redirect: %s", oauth_url)
    return oauth_url


def kiem_tra_trang_thai_oauth(nha_cung_cap: str, state_token: str) -> None:
    try:
        payload = decode_token(state_token, "oauth_state")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phiên đăng nhập OAuth không hợp lệ") from exc
    if payload.get("sub") != nha_cung_cap:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phiên đăng nhập OAuth không hợp lệ")


async def doi_ma_lay_ho_so(nha_cung_cap: str, code: str) -> OAuthProfile:
    config = cau_hinh_nha_cung_cap(nha_cung_cap)
    token_payload = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
        "code": code,
    }
    if nha_cung_cap == "google":
        token_payload["grant_type"] = "authorization_code"

    async with httpx.AsyncClient(timeout=15) as client:
        if nha_cung_cap == "facebook":
            token_response = await client.get(config["token_url"], params=token_payload)
        else:
            token_response = await client.post(config["token_url"], data=token_payload)
        if token_response.is_error:
            if nha_cung_cap == "facebook":
                logger.error(
                    "Facebook token exchange thất bại: status=%s response=%s",
                    token_response.status_code,
                    token_response.text,
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đăng nhập {nhan_nha_cung_cap(nha_cung_cap)} thất bại.",
            )
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đăng nhập {nhan_nha_cung_cap(nha_cung_cap)} thất bại.",
            )

        if nha_cung_cap == "google":
            profile_response = await client.get(
                config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
        else:
            profile_response = await client.get(
                config["userinfo_url"],
                params={
                    "access_token": access_token,
                    "fields": "id,name,email,picture",
                },
            )

    if profile_response.is_error:
        if nha_cung_cap == "facebook":
            logger.error(
                "Facebook Graph API thất bại: status=%s response=%s",
                profile_response.status_code,
                profile_response.text,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Đăng nhập {nhan_nha_cung_cap(nha_cung_cap)} thất bại.",
        )

    data = profile_response.json()
    nha_cung_cap_id = str(data.get("sub") or data.get("id") or "")
    email = str(data.get("email") or "").strip().lower()
    if nha_cung_cap == "facebook" and nha_cung_cap_id and not email:
        email = f"facebook_{nha_cung_cap_id}@sunlens.local"
    ho_ten = str(data.get("name") or email.split("@")[0] or "SunLens User").strip()
    picture = data.get("picture")
    anh_dai_dien = picture.get("data", {}).get("url") if isinstance(picture, dict) else picture

    if not nha_cung_cap_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không lấy được thông tin tài khoản {nhan_nha_cung_cap(nha_cung_cap)}.",
        )
    return OAuthProfile(nha_cung_cap, nha_cung_cap_id, email, ho_ten, anh_dai_dien)


def _random_username(db: Session, nha_cung_cap: str) -> str:
    while True:
        username = f"{nha_cung_cap}_{token_urlsafe(8).replace('-', '').replace('_', '')[:12]}"
        if not db.scalar(select(TaiKhoan).where(TaiKhoan.dang_nhap == username)):
            return username


def dang_nhap_hoac_tao_khach_hang_oauth(db: Session, profile: OAuthProfile) -> TokenPhanHoi:
    account = db.scalar(
        select(TaiKhoan).where(
            TaiKhoan.nha_cung_cap == profile.nha_cung_cap,
            TaiKhoan.nha_cung_cap_id == profile.nha_cung_cap_id,
        )
    )
    if not account:
        account = db.scalar(select(TaiKhoan).join(KhachHang).where(KhachHang.email == profile.email))

    if account:
        if account.trang_thai and account.trang_thai != TAI_KHOAN_HOAT_DONG:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email đã bị khóa.")
        account.nha_cung_cap = profile.nha_cung_cap
        account.nha_cung_cap_id = profile.nha_cung_cap_id
        account.anh_dai_dien = profile.anh_dai_dien
        if account.customer:
            account.customer.ho_ten = account.customer.ho_ten or profile.ho_ten
            account.customer.email = account.customer.email or profile.email
        db.add(account)
        db.commit()
        return tao_phan_hoi_token(account.id_tai_khoan)

    account = TaiKhoan(
        dang_nhap=_random_username(db, profile.nha_cung_cap),
        mat_khau=hash_password(token_urlsafe(32)),
        vai_tro=VAI_TRO_KHACH_HANG,
        trang_thai=TAI_KHOAN_HOAT_DONG,
        key=True,
        nha_cung_cap=profile.nha_cung_cap,
        nha_cung_cap_id=profile.nha_cung_cap_id,
        anh_dai_dien=profile.anh_dai_dien,
    )
    db.add(account)
    db.flush()
    db.add(
        KhachHang(
            id_tai_khoan=account.id_tai_khoan,
            ho_ten=profile.ho_ten,
            email=profile.email,
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng",
        ) from exc
    return tao_phan_hoi_token(account.id_tai_khoan)
