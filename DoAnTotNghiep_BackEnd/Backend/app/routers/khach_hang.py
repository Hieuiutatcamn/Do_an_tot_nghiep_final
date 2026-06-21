from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.khach_hang import KhachHangTao, KhachHangPhanHoi, KhachHangCapNhat
from app.services import khach_hang_service
from app.utils.config import BACKEND_DIR, get_settings
from app.utils.dependencies import get_current_account, require_admin
from app.utils.pagination import Page, PaginationParams, build_page

router = APIRouter(prefix="/khach-hang", tags=["Khách hàng"])

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
ALLOWED_CCCD_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
CCCD_SIDE_CONFIG = {
    "front": ("cccd_front", "anh_cccd_mat_truoc"),
    "back": ("cccd_back", "anh_cccd_mat_sau"),
}


def account_can_access_customer(account: TaiKhoan, customer_id: int) -> bool:
    return account.vai_tro == "Admin" or (
        account.customer is not None
        and account.customer.id_khach_hang == customer_id
    )


def require_customer_access(account: TaiKhoan, customer_id: int) -> None:
    if not account_can_access_customer(account, customer_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KhachHang access is required",
        )


def update_payload_for_account(account: TaiKhoan, payload: KhachHangCapNhat) -> KhachHangCapNhat:
    if account.vai_tro == "Admin":
        return payload

    data = payload.model_dump(exclude_unset=True)
    data.pop("id_tai_khoan", None)
    return KhachHangCapNhat(**data)


@router.get("", response_model=Page[KhachHangPhanHoi])
def lay_danh_sach_khach_hang(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> Page[KhachHangPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = khach_hang_service.lay_danh_sach_khach_hang(db, params)
    return build_page(items, total, params)


@router.get("/{customer_id}", response_model=KhachHangPhanHoi)
def lay_khach_hang(
    customer_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    require_customer_access(account, customer_id)
    return khach_hang_service.tim_kiem_khach_hang(db, customer_id)


@router.post("", response_model=KhachHangPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_khach_hang(
    payload: KhachHangTao,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return khach_hang_service.tao_khach_hang(db, payload)


@router.put("/{customer_id}", response_model=KhachHangPhanHoi)
def cap_nhat_khach_hang(
    customer_id: int,
    payload: KhachHangCapNhat,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
):
    require_customer_access(account, customer_id)
    return khach_hang_service.cap_nhat_khach_hang(db, customer_id, update_payload_for_account(account, payload))


@router.post("/{customer_id}/cccd-image", response_model=KhachHangPhanHoi)
async def upload_customer_cccd_image(
    customer_id: int,
    db: Annotated[Session, Depends(get_db)],
    account: Annotated[TaiKhoan, Depends(get_current_account)],
    side: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
):
    require_customer_access(account, customer_id)
    khach_hang_service.tim_kiem_khach_hang(db, customer_id)
    if side not in CCCD_SIDE_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="side phải là front hoặc back",
        )

    extension = ALLOWED_CCCD_IMAGE_TYPES.get(file.content_type or "")
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

    prefix, field_name = CCCD_SIDE_CONFIG[side]
    FRONTEND_USER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in FRONTEND_USER_IMAGE_DIR.glob(f"{prefix}_{customer_id}.*"):
        if old_file.is_file():
            old_file.unlink()

    file_name = f"{prefix}_{customer_id}{extension}"
    target_path = FRONTEND_USER_IMAGE_DIR / file_name
    target_path.write_bytes(content)

    image_path = f"{PUBLIC_USER_IMAGE_PREFIX}/{file_name}"
    return khach_hang_service.cap_nhat_khach_hang(
        db,
        customer_id,
        KhachHangCapNhat(**{field_name: image_path}),
    )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_khach_hang(
    customer_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
) -> None:
    khach_hang_service.xoa_khach_hang(db, customer_id)


legacy_router = tao_router_ke_thua(router, "/customers", tags=["Khách hàng legacy"])
