#!/bin/sh
# Entrypoint backend: cho MySQL san sang -> chay migration -> khoi dong app.
set -e

echo "[entrypoint] Cho MySQL san sang..."
python - <<'PY'
import sys, time
import pymysql
from app.utils.config import get_settings

s = get_settings()
last_err = None
for i in range(60):
    try:
        conn = pymysql.connect(
            host=s.db_host,
            port=int(s.db_port),
            user=s.db_user,
            password=s.db_password,
            database=s.db_name,
            connect_timeout=3,
        )
        conn.close()
        print("[entrypoint] Ket noi MySQL OK.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        last_err = exc
        print(f"[entrypoint] ({i + 1}/60) chua ket noi duoc MySQL, thu lai sau 2s...")
        time.sleep(2)

print(f"[entrypoint] Khong the ket noi MySQL: {last_err}", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] Chay alembic upgrade head (ap dung migration 0019 -> 0021)..."
alembic upgrade head

echo "[entrypoint] Khoi dong ung dung..."
exec "$@"
