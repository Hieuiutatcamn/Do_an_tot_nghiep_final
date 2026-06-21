# Backend FastAPI - Sunlens Camera
# Python 3.12 (khop voi .venv goc va bytecode cpython-312 trong repo)
FROM python:3.12-slim

# tzdata: code dung datetime.now() (naive) -> phai co mui gio VN cho dung
# (logic het han thanh toan VNPay gia dinh UTC+7)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Ho_Chi_Minh

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# QUAN TRONG: bo tri thu muc PHAI giong repo.
# 3 router (thiet_bi/khach_hang/nguoi_dung) ghi anh ra:
#   BACKEND_DIR.parent.parent / "DOANTOTNGHIEP_FrontEnd" / "Webthuemayanh_FE" / ...
# Voi BACKEND_DIR = /workspace/DoAnTotNghiep_BackEnd/Backend  ->  parent.parent = /workspace
# Nho do anh ghi ra /workspace/DOANTOTNGHIEP_FrontEnd (volume chung voi nginx).
WORKDIR /workspace/DoAnTotNghiep_BackEnd/Backend

# Cai dependencies truoc de tan dung cache layer
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy ma nguon backend (xem .dockerignore - khong copy .venv/.env/log)
COPY . .

# Chuan hoa line-ending + cap quyen chay cho entrypoint (file tao tren Windows co the la CRLF)
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000

# Healthcheck goi /health bang python (slim khong co curl)
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3).status==200 else 1)" || exit 1

# Entrypoint: cho DB -> alembic upgrade head -> chay uvicorn (1 worker)
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
