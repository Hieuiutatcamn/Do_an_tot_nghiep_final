from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, MySQLDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Sunlens Camera API"
    app_env: str = "development"
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "do_an_tot_nghiep"

    jwt_secret_key: str = Field(min_length=16)
    jwt_refresh_secret_key: str = Field(min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    reset_password_token_expire_minutes: int = 30

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 5
    backend_public_url: str = "http://127.0.0.1:8000"
    frontend_url: str = "http://127.0.0.1:5500"
    oauth_frontend_login_url: str | None = None
    reset_password_frontend_url: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None
    facebook_client_id: str | None = None
    facebook_client_secret: str | None = None
    facebook_api_version: str = "v22.0"
    facebook_redirect_uri: str | None = None
    facebook_frontend_success_url: str = (
        "http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dang_nhap.html"
    )
    vnpay_tmn_code: str = ""
    vnpay_hash_secret: str = ""
    vnpay_payment_url: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    vnpay_return_url: str = (
        "http://127.0.0.1:5500/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/ket_qua_thanh_toan.html"
    )
    vnpay_ipn_url: str = ""
    vnpay_deposit_amount: int = 200000
    vnpay_payment_expire_minutes: int = 15
    vnpay_expiration_scan_seconds: int = 30
    resend_api_key: str = ""
    email_from: str = "SunLens Camera <onboarding@resend.dev>"
    email_admin: str = ""
    resend_test_recipient: str = ""
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> MySQLDsn:
        password = f":{self.db_password}" if self.db_password else ""
        return MySQLDsn.build(
            scheme="mysql+pymysql",
            username=self.db_user,
            password=password[1:] if password else None,
            host=self.db_host,
            port=self.db_port,
            path=self.db_name,
        )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if path.is_absolute():
            return path
        return BACKEND_DIR / path

    def sqlalchemy_database_url(self) -> str:
        return str(self.database_url)

    def cors_origins_value(self) -> list[str]:
        if "*" in self.cors_origins:
            return ["*"]
        return self.cors_origins

    def oauth_frontend_login_url_value(self) -> str:
        if self.oauth_frontend_login_url:
            return self.oauth_frontend_login_url
        return (
            f"{self.frontend_url.rstrip('/')}"
            "/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dang_nhap.html"
        )

    def oauth_callback_url(self, nha_cung_cap: str) -> str:
        if nha_cung_cap == "google" and self.google_redirect_uri:
            return self.google_redirect_uri
        if nha_cung_cap == "facebook":
            return self.facebook_redirect_uri or ""
        return f"{self.backend_public_url.rstrip('/')}/api/v1/auth/{nha_cung_cap}/callback"

    def reset_password_frontend_url_value(self) -> str:
        if self.reset_password_frontend_url:
            return self.reset_password_frontend_url
        return (
            f"{self.frontend_url.rstrip('/')}"
            "/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dat_lai_mat_khau.html"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
