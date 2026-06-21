import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database.session import get_db
from app.routers import (
    danh_muc,
    don_hang,
    don_thue,
    email,
    gio_hang,
    khach_hang,
    khieu_nai,
    ma_giam_gia,
    nguoi_dung,
    nhan_vien,
    tai_khoan,
    thiet_bi,
    thong_bao,
    thanh_toan,
    tro_chuyen,
    xac_thuc,
)
from app.services import het_han_thanh_toan_service
from app.utils.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _huy_don_vnpay_het_han_voi_dependency(app_instance: FastAPI) -> int:
    dependency = app_instance.dependency_overrides.get(get_db, get_db)
    generator = dependency()
    db = next(generator)
    try:
        return het_han_thanh_toan_service.huy_cac_don_vnpay_het_han(db)
    finally:
        close = getattr(generator, "close", None)
        if close:
            close()


async def _quet_don_vnpay_het_han_dinh_ky(app_instance: FastAPI) -> None:
    while True:
        try:
            await asyncio.to_thread(
                _huy_don_vnpay_het_han_voi_dependency,
                app_instance,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Không thể quét đơn VNPAY hết hạn.")
        await asyncio.sleep(settings.vnpay_expiration_scan_seconds)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    task = asyncio.create_task(_quet_don_vnpay_het_han_dinh_ky(app_instance))
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
    description="Backend FastAPI cho he thong thue thiet bi may anh.",
    docs_url=None,
    lifespan=lifespan,
)


@app.get("/docs", include_in_schema=False)
def swagger_ui() -> HTMLResponse:
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_ui_parameters=app.swagger_ui_parameters,
    )
    html = response.body.decode("utf-8").replace(
        "</head>",
        "<style>.swagger-ui .info .main > .link { display: none; }</style></head>",
    )
    return HTMLResponse(html)


@app.middleware("http")
async def dong_bo_don_vnpay_het_han(request: Request, call_next):
    if request.url.path.startswith("/api/v1/"):
        try:
            await asyncio.to_thread(
                _huy_don_vnpay_het_han_voi_dependency,
                request.app,
            )
        except Exception:
            logger.exception("Không thể đồng bộ đơn VNPAY hết hạn trước yêu cầu API.")
    return await call_next(request)


@app.middleware("http")
async def ensure_utf8_json_response(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Lỗi chưa được xử lý tại %s %s", request.method, request.url.path)
        response = JSONResponse(
            status_code=500,
            content={
                "detail": (
                    "Lỗi máy chủ khi xử lý yêu cầu. "
                    "Giao dịch đã được hoàn tác, vui lòng thử lại."
                )
            },
        )
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json") and "charset=" not in content_type.lower():
        response.headers["content-type"] = f"{content_type}; charset=utf-8"
    return response


cors_origins = list(
    dict.fromkeys(
        [
            "http://127.0.0.1:5500",
            "http://localhost:5500",
            *settings.cors_origins_value(),
        ]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = settings.upload_path()
upload_path.mkdir(parents=True, exist_ok=True)
app.mount(f"/{settings.upload_dir}", StaticFiles(directory=upload_path), name=settings.upload_dir)

API_PREFIX = "/api/v1"
app.include_router(xac_thuc.router, prefix=API_PREFIX)
app.include_router(nguoi_dung.router, prefix=API_PREFIX)
app.include_router(tai_khoan.router, prefix=API_PREFIX)
app.include_router(danh_muc.router, prefix=API_PREFIX)
app.include_router(khach_hang.router, prefix=API_PREFIX)
app.include_router(thiet_bi.router, prefix=API_PREFIX)
app.include_router(nhan_vien.router, prefix=API_PREFIX)
app.include_router(don_thue.router, prefix=API_PREFIX)
app.include_router(don_hang.router, prefix=API_PREFIX)
app.include_router(don_hang.chi_tiet_don_hang_router, prefix=API_PREFIX)
app.include_router(email.router, prefix=API_PREFIX)
app.include_router(khieu_nai.router, prefix=API_PREFIX)
app.include_router(khieu_nai.admin_router, prefix=API_PREFIX)
app.include_router(ma_giam_gia.router, prefix=API_PREFIX)
app.include_router(ma_giam_gia.admin_router, prefix=API_PREFIX)
app.include_router(tro_chuyen.router, prefix=API_PREFIX)
app.include_router(tro_chuyen.admin_router, prefix=API_PREFIX)
app.include_router(gio_hang.router, prefix=API_PREFIX)
app.include_router(thong_bao.router, prefix=API_PREFIX)
app.include_router(thanh_toan.router, prefix=API_PREFIX)
app.include_router(thanh_toan.router_tuong_thich, prefix=API_PREFIX)

app.include_router(xac_thuc.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(nguoi_dung.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(tai_khoan.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(danh_muc.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(khach_hang.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(thiet_bi.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(nhan_vien.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(don_thue.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(don_hang.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(don_hang.legacy_chi_tiet_don_hang_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(khieu_nai.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(khieu_nai.legacy_admin_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(ma_giam_gia.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(ma_giam_gia.legacy_admin_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(tro_chuyen.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(gio_hang.legacy_router, prefix=API_PREFIX, include_in_schema=False)
app.include_router(thong_bao.legacy_router, prefix=API_PREFIX, include_in_schema=False)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
