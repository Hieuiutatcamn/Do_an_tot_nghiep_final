from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.models.khach_hang import KhachHang
from app.schemas.xac_thuc import TaiKhoanPhanHoi, HoSoKhachHangPhanHoi, ToiPhanHoi
from app.schemas.khach_hang import KhachHangPhanHoi, KhachHangCapNhat
from app.services import khach_hang_service
from app.utils.config import BACKEND_DIR, get_settings
from app.utils.dependencies import get_current_account

router = APIRouter(prefix="/nguoi-dung", tags=["Người dùng"])

FRONTEND_USER_IMAGE_DIR = (
    BACKEND_DIR.parent.parent
    / "DOANTOTNGHIEP_FrontEnd"
    / "Webthuemayanh_FE"
    / "user"
    / "Sunlens_Camera"
    / "assets"
    / "images"
    / "user"
)
PUBLIC_USER_IMAGE_PREFIX = "assets/images/user"
ALLOWED_USER_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
USER_IMAGE_SIDE_CONFIG = {
    "anh_dai_dien": ("cccd_anh_dai_dien", "anh_dai_dien"),
    "front": ("cccd_front", "anh_cccd_mat_truoc"),
    "back": ("cccd_back", "anh_cccd_mat_sau"),
}


def build_me_response(account: TaiKhoan, customer: KhachHang | None = None) -> ToiPhanHoi:
    active_customer = customer if customer is not None else account.customer
    return ToiPhanHoi(
        account=TaiKhoanPhanHoi.model_validate(account),
        customer=HoSoKhachHangPhanHoi.model_validate(active_customer) if active_customer else None,
        id=account.id_tai_khoan,
        ho_ten=active_customer.ho_ten if active_customer else None,
        email=active_customer.email if active_customer else None,
        anh_dai_dien=account.anh_dai_dien,
        nha_cung_cap=account.nha_cung_cap or "local",
    )


def require_customer_profile(account: TaiKhoan) -> KhachHang:
    if not account.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KhachHang profile is required",
        )
    return account.customer


def self_update_payload(payload: KhachHangCapNhat) -> KhachHangCapNhat:
    data = payload.model_dump(exclude_unset=True)
    data.pop("id_tai_khoan", None)
    return KhachHangCapNhat(**data)


async def save_user_image(
    db: Session,
    account: TaiKhoan,
    customer: KhachHang,
    side: str,
    file: UploadFile,
) -> KhachHang | ToiPhanHoi:
    if side not in USER_IMAGE_SIDE_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="side phải là anh_dai_dien, front hoặc back",
        )

    extension = ALLOWED_USER_IMAGE_TYPES.get(file.content_type or "")
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ ảnh JPG, PNG và WEBP",
        )

    content = await file.read()
    settings = get_settings()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File lớn hơn {settings.max_upload_size_mb}MB",
        )

    prefix, field_name = USER_IMAGE_SIDE_CONFIG[side]
    customer_id = customer.id_khach_hang
    FRONTEND_USER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in FRONTEND_USER_IMAGE_DIR.glob(f"{prefix}_{customer_id}.*"):
        if old_file.is_file():
            old_file.unlink()

    file_name = f"{prefix}_{customer_id}{extension}"
    target_path = FRONTEND_USER_IMAGE_DIR / file_name
    target_path.write_bytes(content)

    image_path = f"{PUBLIC_USER_IMAGE_PREFIX}/{file_name}"
    if side == "anh_dai_dien":
        account.anh_dai_dien = image_path
        db.add(account)
        db.commit()
        db.refresh(account)
        return build_me_response(account, customer)

    return khach_hang_service.cap_nhat_khach_hang(
        db,
        customer_id,
        KhachHangCapNhat(**{field_name: image_path}),
    )


@router.get("/me", response_model=ToiPhanHoi)
def get_my_profile(account: Annotated[TaiKhoan, Depends(get_current_account)]) -> ToiPhanHoi:
    return build_me_response(account)


@router.put("/me", response_model=ToiPhanHoi)
def update_my_profile(
    payload: KhachHangCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
) -> ToiPhanHoi:
    customer = require_customer_profile(account)
    updated_customer = khach_hang_service.cap_nhat_khach_hang(
        db,
        customer.id_khach_hang,
        self_update_payload(payload),
    )
    return build_me_response(account, updated_customer)


@router.post("/me/cccd-image", response_model=KhachHangPhanHoi)
async def upload_my_profile_image(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    side: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
):
    customer = require_customer_profile(account)
    ket_qua = await save_user_image(db, account, customer, side, file)
    if isinstance(ket_qua, ToiPhanHoi):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="side phải là front hoặc back khi dùng /me/cccd-image",
        )
    return ket_qua


@router.post("/upload-cccd", response_model=KhachHangPhanHoi)
async def upload_current_user_cccd_image(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    side: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    user_id: Annotated[str | None, Form()] = None,
):
    customer = require_customer_profile(account)
    ket_qua = await save_user_image(db, account, customer, side, file)
    if isinstance(ket_qua, ToiPhanHoi):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="side phải là front hoặc back khi dùng /upload-cccd",
        )
    return ket_qua


@router.post("/upload-anh_dai_dien", response_model=ToiPhanHoi)
async def upload_current_user_anh_dai_dien(
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    file: Annotated[UploadFile, File(...)],
    user_id: Annotated[str | None, Form()] = None,
):
    customer = require_customer_profile(account)
    ket_qua = await save_user_image(db, account, customer, "anh_dai_dien", file)
    if not isinstance(ket_qua, ToiPhanHoi):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể cập nhật ảnh đại diện.",
        )
    return ket_qua


legacy_router = tao_router_ke_thua(router, "/users", tags=["Người dùng legacy"])
