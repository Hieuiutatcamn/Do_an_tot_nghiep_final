import json
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.router_ke_thua import tao_router_ke_thua
from app.models.tai_khoan import TaiKhoan
from app.schemas.thiet_bi import (
    KhaDungThietBiPhanHoi,
    ThietBiKhaDungPhanHoi,
    ThietBiTao,
    ThietBiPhanHoi,
    ThietBiCapNhat,
)
from app.services import kiem_tra_lich_thue_service, thiet_bi_service
from app.utils.config import BACKEND_DIR, get_settings
from app.utils.dependencies import require_admin
from app.utils.pagination import Page, PaginationParams, build_page
from app.utils.upload import save_upload_file

router = APIRouter(prefix="/thiet-bi", tags=["Thiết bị"])

FRONTEND_PRODUCT_IMAGE_DIR = (
    BACKEND_DIR.parent.parent
    / "DOANTOTNGHIEP_FrontEnd"
    / "Webthuemayanh_FE"
    / "user"
    / "Sunlens_Camera"
    / "assets"
    / "images"
    / "product"
)
PUBLIC_PRODUCT_IMAGE_PREFIX = "assets/images/product"
ALLOWED_PRODUCT_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _product_image_extension(image: UploadFile) -> str:
    content_type = (image.content_type or "").lower()
    extension = ALLOWED_PRODUCT_IMAGE_TYPES.get(content_type)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ ảnh JPG, PNG hoặc WEBP.",
        )
    return extension


def _parse_kept_product_images(raw_value: str, id_thiet_bi: int) -> list[str]:
    if not raw_value:
        return []

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách ảnh giữ lại không hợp lệ.",
        ) from exc

    if not isinstance(parsed, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách ảnh giữ lại phải là mảng.",
        )

    kept_images: list[str] = []
    for item in parsed:
        image_path = str(item or "").strip().replace("\\", "/")
        if not image_path:
            continue
        if not image_path.startswith(f"{PUBLIC_PRODUCT_IMAGE_PREFIX}/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đường dẫn ảnh giữ lại không hợp lệ.",
            )

        filename = image_path.rsplit("/", 1)[-1]
        if filename.startswith(f"device_") and not filename.startswith(f"device_{id_thiet_bi}_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ảnh giữ lại không thuộc thiết bị hiện tại.",
            )
        if image_path not in kept_images:
            kept_images.append(image_path)

    return kept_images


@router.get("", response_model=Page[ThietBiPhanHoi])
def lay_danh_sach_thiet_bi(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    search: str | None = None,
    category_id: int | None = None,
    category: Annotated[list[str] | None, Query()] = None,
    categories: str | None = None,
    status: Annotated[list[str] | None, Query()] = None,
    statuses: str | None = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    sort: str | None = None,
    available_only: bool = False,
) -> Page[ThietBiPhanHoi]:
    params = PaginationParams(page=page, page_size=page_size)
    items, total = thiet_bi_service.lay_danh_sach_thiet_bi(
        db,
        params,
        search=search,
        category_id=category_id,
        category=category,
        categories=categories,
        status=status,
        statuses=statuses,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        available_only=available_only,
    )
    return build_page(items, total, params)


@router.get("/available", response_model=list[ThietBiKhaDungPhanHoi])
def lay_thiet_bi_kha_dung(
    db: Annotated[Session, Depends(get_db)],
    ngay_nhan: Annotated[date, Query()],
    ngay_tra: Annotated[date, Query()],
    search: str | None = None,
    category_id: int | None = None,
    category: Annotated[list[str] | None, Query()] = None,
    categories: str | None = None,
    status: Annotated[list[str] | None, Query()] = None,
    statuses: str | None = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    sort: str | None = None,
) -> list[ThietBiKhaDungPhanHoi]:
    return [
        ThietBiKhaDungPhanHoi(**item)
        for item in thiet_bi_service.lay_thiet_bi_kha_dung(
            db,
            ngay_nhan=ngay_nhan,
            ngay_tra=ngay_tra,
            search=search,
            category_id=category_id,
            category=category,
            categories=categories,
            status=status,
            statuses=statuses,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
        )
    ]


@router.get("/{id_thiet_bi}", response_model=ThietBiPhanHoi)
def lay_thiet_bi(id_thiet_bi: int, db: Annotated[Session, Depends(get_db)]):
    return thiet_bi_service.lay_thiet_bi_hoac_404(db, id_thiet_bi)


@router.get("/{id_thiet_bi}/availability", response_model=KhaDungThietBiPhanHoi)
def lay_kha_dung_thiet_bi(
    id_thiet_bi: int,
    db: Annotated[Session, Depends(get_db)],
    ngay_nhan: Annotated[date | None, Query()] = None,
    ngay_tra: Annotated[date | None, Query()] = None,
    so_luong: Annotated[int, Query(gt=0)] = 1,
):
    device = thiet_bi_service.lay_thiet_bi_hoac_404(db, id_thiet_bi)
    if ngay_nhan is None and ngay_tra is None:
        total_quantity = int(device.so_luong or 0)
        return KhaDungThietBiPhanHoi(
            Id_thiet_bi=device.id_thiet_bi,
            id_thiet_bi=device.id_thiet_bi,
            ten_thiet_bi=device.ten_thiet_bi,
            tong_so_luong=total_quantity,
            so_luong_da_dat=0,
            so_luong_kha_dung=total_quantity,
            remaining_quantity=total_quantity,
            available=total_quantity >= so_luong,
            so_luong=total_quantity,
            con_hang=total_quantity > 0,
            message="Có thể thuê" if total_quantity >= so_luong else "Thiết bị hiện không còn số lượng khả dụng.",
            tinh_trang=device.tinh_trang,
        )
    if ngay_nhan is None or ngay_tra is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập đủ ngày nhận và ngày trả.",
        )
    return KhaDungThietBiPhanHoi(
        **kiem_tra_lich_thue_service.tom_tat_kha_dung(
            db,
            device.id_thiet_bi,
            ngay_nhan,
            ngay_tra,
            requested_quantity=so_luong,
            device=device,
        )
    )


@router.post("", response_model=ThietBiPhanHoi, status_code=status.HTTP_201_CREATED)
def tao_thiet_bi(
    payload: ThietBiTao,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return thiet_bi_service.tao_thiet_bi(db, payload)


@router.put("/{id_thiet_bi}", response_model=ThietBiPhanHoi)
def cap_nhat_thiet_bi(
    id_thiet_bi: int,
    payload: ThietBiCapNhat,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
):
    return thiet_bi_service.cap_nhat_thiet_bi(db, id_thiet_bi, payload)


@router.post("/{id_thiet_bi}/image", response_model=ThietBiPhanHoi)
async def tai_len_anh_thiet_bi(
    id_thiet_bi: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
    image: Annotated[UploadFile, File(...)],
):
    thiet_bi_service.lay_thiet_bi_hoac_404(db, id_thiet_bi)
    image_path = await save_upload_file(image, f"devices/{id_thiet_bi}")
    return thiet_bi_service.cap_nhat_anh_thiet_bi(db, id_thiet_bi, image_path)


@router.post("/{id_thiet_bi}/images", response_model=ThietBiPhanHoi)
async def tai_len_nhieu_anh_thiet_bi(
    id_thiet_bi: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
    existing_images: Annotated[str, Form()] = "[]",
    images: Annotated[list[UploadFile] | None, File()] = None,
):
    thiet_bi_service.lay_thiet_bi_hoac_404(db, id_thiet_bi)
    kept_images = _parse_kept_product_images(existing_images, id_thiet_bi)
    upload_images = images or []

    if len(kept_images) + len(upload_images) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mỗi thiết bị chỉ nên upload tối đa 20 ảnh.",
        )

    settings = get_settings()
    pending_files: list[tuple[str, bytes]] = []
    for image in upload_images:
        extension = _product_image_extension(image)
        content = await image.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {image.filename or 'ảnh'} đang rỗng.",
            )
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {image.filename or 'ảnh'} vượt quá {settings.max_upload_size_mb}MB.",
            )
        pending_files.append((extension, content))

    FRONTEND_PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    kept_filenames = {
        path.rsplit("/", 1)[-1]
        for path in kept_images
        if path.startswith(f"{PUBLIC_PRODUCT_IMAGE_PREFIX}/")
    }
    kept_stems = {filename.rsplit(".", 1)[0] for filename in kept_filenames}
    for old_file in FRONTEND_PRODUCT_IMAGE_DIR.glob(f"device_{id_thiet_bi}_*"):
        if old_file.is_file() and old_file.name not in kept_filenames:
            old_file.unlink()

    image_paths: list[str] = kept_images[:]
    next_index = 1
    for extension, content in pending_files:
        while True:
            stem = f"device_{id_thiet_bi}_{next_index}"
            filename = f"{stem}{extension}"
            target_path = FRONTEND_PRODUCT_IMAGE_DIR / filename
            next_index += 1
            if stem not in kept_stems and not target_path.exists():
                break
        target_path.write_bytes(content)
        image_paths.append(f"{PUBLIC_PRODUCT_IMAGE_PREFIX}/{filename}")

    image_payload = json.dumps(image_paths, ensure_ascii=False)
    return thiet_bi_service.cap_nhat_anh_thiet_bi(db, id_thiet_bi, image_payload)


@router.delete("/{id_thiet_bi}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_thiet_bi(
    id_thiet_bi: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[TaiKhoan, Depends(require_admin)],
) -> None:
    thiet_bi_service.xoa_thiet_bi(db, id_thiet_bi)


legacy_router = tao_router_ke_thua(router, "/devices", tags=["Thiết bị legacy"])
