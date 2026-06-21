from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.tai_khoan import TaiKhoan
from app.services import gui_email_service
from app.utils.config import get_settings
from app.utils.dependencies import require_admin

router = APIRouter(prefix="/email", tags=["Email"])


@router.get("/test")
def gui_email_kiem_thu(
    _: Annotated[TaiKhoan, Depends(require_admin)],
) -> dict[str, str | None]:
    settings = get_settings()
    loi_cau_hinh = gui_email_service.lay_loi_cau_hinh_email(settings)
    if loi_cau_hinh:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=loi_cau_hinh,
        )

    gui_email_service.ma_email_resend_gan_nhat = None
    da_gui = gui_email_service.gui_email(
        settings.email_admin,
        "SunLens Camera - Email kiểm thử",
        gui_email_service._khung_email(
            "Email kiểm thử",
            "<p>Resend API đã được kết nối thành công với hệ thống SunLens Camera.</p>",
        ),
    )
    if not da_gui:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể gửi email test qua Resend. Vui lòng kiểm tra log máy chủ.",
        )
    return {
        "message": "Đã gửi email test.",
        "ma_email_resend": gui_email_service.ma_email_resend_gan_nhat,
    }
