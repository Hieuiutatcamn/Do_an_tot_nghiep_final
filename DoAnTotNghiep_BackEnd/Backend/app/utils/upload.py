from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.utils.config import get_settings

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


async def save_upload_file(upload_file: UploadFile, folder: str) -> str:
    settings = get_settings()
    extension = Path(upload_file.filename or "").suffix.lower()
    expected_extension = ALLOWED_IMAGE_TYPES.get(upload_file.content_type or "")
    if not expected_extension or extension not in ALLOWED_IMAGE_TYPES.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng chọn file ảnh hợp lệ dưới 5MB.",
        )

    content = await upload_file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Vui lòng chọn file ảnh hợp lệ dưới 5MB.",
        )

    extension = expected_extension
    file_name = f"{uuid4().hex}{extension}"
    target_dir = Path(settings.upload_dir) / folder
    if not target_dir.is_absolute():
        target_dir = settings.upload_path() / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / file_name
    file_path.write_bytes(content)
    return f"/{settings.upload_dir}/{folder}/{file_name}"


def delete_upload_file(public_path: str) -> None:
    settings = get_settings()
    public_prefix = f"/{settings.upload_dir}/"
    if not public_path.startswith(public_prefix):
        return

    upload_root = settings.upload_path().resolve()
    target_path = (upload_root / public_path.removeprefix(public_prefix)).resolve()
    if upload_root not in target_path.parents:
        return
    if target_path.is_file():
        target_path.unlink()
