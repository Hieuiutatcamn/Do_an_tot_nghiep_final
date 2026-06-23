import asyncio
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException, status

from app.services import dang_nhap_xa_hoi_service
from app.services.xac_thuc_service import tao_token_dat_lai_mat_khau
from app.utils.config import get_settings
from app.utils.security import create_token, decode_token
from app.services.dang_nhap_xa_hoi_service import OAuthProfile
from app.utils.security import create_oauth_state
from tests.conftest import auth_headers


def test_register_login_and_refresh(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "kh02",
            "password": "123456",
            "ho_ten": "Tran Thi B",
            "sdt": "0912222222",
            "email": "b@example.com",
        },
    )
    assert register_response.status_code == 201, register_response.text
    register_data = register_response.json()
    assert register_data["token_type"] == "bearer"
    assert register_data["access_token"]
    assert register_data["refresh_token"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "kh02", "password": "123456"},
    )
    assert login_response.status_code == 200, login_response.text

    vietnamese_login_response = client.post(
        "/api/v1/auth/login",
        json={"ten_dang_nhap": "kh02", "mat_khau": "123456"},
    )
    assert vietnamese_login_response.status_code == 200, vietnamese_login_response.text

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    assert refresh_response.json()["access_token"]


def test_register_supports_multipart_with_cccd_images(client, monkeypatch):
    saved_files = []

    async def fake_save_upload_file(upload_file, folder):
        saved_files.append((upload_file.filename, folder))
        return f"/uploads/{folder}/{upload_file.filename}"

    monkeypatch.setattr("app.routers.xac_thuc.save_upload_file", fake_save_upload_file)
    response = client.post(
        "/api/v1/auth/register",
        data={
            "username": "kh03",
            "password": "123456",
            "ho_ten": "Le Van C",
            "sdt": "0913333333",
            "cccd": "001001000033",
            "email": "c@example.com",
        },
        files={
            "cccd_truoc": ("front.jpg", b"front", "image/jpeg"),
            "cccd_sau": ("back.webp", b"back", "image/webp"),
        },
    )

    assert response.status_code == 201, response.text
    assert saved_files == [("front.jpg", "cccd"), ("back.webp", "cccd")]


def test_register_supports_legacy_multipart_field_names_from_frontend(client, monkeypatch):
    saved_files = []

    async def fake_save_upload_file(upload_file, folder):
        saved_files.append((upload_file.filename, folder))
        return f"/uploads/{folder}/{upload_file.filename}"

    monkeypatch.setattr("app.routers.xac_thuc.save_upload_file", fake_save_upload_file)
    response = client.post(
        "/api/v1/auth/register",
        data={
            "ten_dang_nhap": "kh031",
            "mat_khau": "123456",
            "ho_ten": "Le Van C Legacy",
            "sdt": "0913333334",
            "cccd": "001001000034",
            "thu_dien_tu": "c-legacy@example.com",
        },
        files={
            "anh_cccd_mat_truoc": ("front-legacy.jpg", b"front", "image/jpeg"),
            "anh_cccd_mat_sau": ("back-legacy.webp", b"back", "image/webp"),
        },
    )

    assert response.status_code == 201, response.text
    assert saved_files == [("front-legacy.jpg", "cccd"), ("back-legacy.webp", "cccd")]


def test_register_reports_all_duplicate_fields(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "kh01",
            "password": "123456",
            "ho_ten": "Duplicate KhachHang",
            "sdt": "0911111111",
            "email": "a@example.com",
        },
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == [
        "Tên đăng nhập đã tồn tại",
        "Số điện thoại đã được sử dụng",
        "Email đã được sử dụng",
    ]


def test_seed_plaintext_password_login_is_supported(client):
    headers = auth_headers(client)
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["account"]["dang_nhap"] == "kh01"
    assert me_response.json()["email"] == "a@example.com"
    assert me_response.json()["customer"]["email"] == "a@example.com"


def test_oauth2_token_form_login_is_supported_for_swagger(client):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "kh01", "password": "123456"},
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["account"]["dang_nhap"] == "kh01"


def test_google_oauth_callback_creates_customer_and_returns_tokens(client, monkeypatch):
    async def fake_exchange_code_for_profile(nha_cung_cap, code):
        assert nha_cung_cap == "google"
        assert code == "google-code"
        return OAuthProfile(
            nha_cung_cap="google",
            nha_cung_cap_id="google-user-1",
            email="google@example.com",
            ho_ten="Google User",
            anh_dai_dien="https://example.com/google-anh_dai_dien.jpg",
        )

    monkeypatch.setattr("app.services.dang_nhap_xa_hoi_service.doi_ma_lay_ho_so", fake_exchange_code_for_profile)
    response = client.get(
        f"/api/v1/auth/google/callback?code=google-code&state={create_oauth_state('google')}",
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    redirect_url = urlparse(response.headers["location"])
    assert redirect_url.scheme == "http"
    assert redirect_url.netloc == "127.0.0.1:5500"
    assert redirect_url.path == "/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dang_nhap.html"
    assert response.headers["cache-control"] == "no-store"
    fragment = parse_qs(redirect_url.fragment)
    token = fragment["access_token"][0]
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200, me_response.text
    me = me_response.json()
    assert me["ho_ten"] == "Google User"
    assert me["email"] == "google@example.com"
    assert me["anh_dai_dien"] == "https://example.com/google-anh_dai_dien.jpg"
    assert me["nha_cung_cap"] == "google"


def test_facebook_oauth_callback_links_existing_email(client, monkeypatch):
    async def fake_exchange_code_for_profile(nha_cung_cap, code):
        return OAuthProfile(
            nha_cung_cap="facebook",
            nha_cung_cap_id="facebook-user-1",
            email="a@example.com",
            ho_ten="Facebook User",
            anh_dai_dien="https://example.com/facebook-anh_dai_dien.jpg",
        )

    monkeypatch.setattr("app.services.dang_nhap_xa_hoi_service.doi_ma_lay_ho_so", fake_exchange_code_for_profile)
    response = client.get(
        f"/api/v1/auth/facebook/callback?code=facebook-code&state={create_oauth_state('facebook')}",
        follow_redirects=False,
    )

    assert response.status_code == 302, response.text
    redirect_url = urlparse(response.headers["location"])
    assert redirect_url.scheme == "http"
    assert redirect_url.netloc == "127.0.0.1:5500"
    assert redirect_url.path == "/DOANTOTNGHIEP_FrontEnd/Webthuemayanh_FE/user/Sunlens_Camera/dang_nhap.html"
    fragment = parse_qs(redirect_url.fragment)
    token = fragment["access_token"][0]
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200, me_response.text
    me = me_response.json()
    assert me["account"]["dang_nhap"] == "kh01"
    assert me["nha_cung_cap"] == "facebook"
    assert me["anh_dai_dien"] == "https://example.com/facebook-anh_dai_dien.jpg"


def test_facebook_profile_uses_fallback_email_and_exact_graph_fields(monkeypatch):
    class FakeResponse:
        def __init__(self, data):
            self._data = data
            self.is_error = False
            self.status_code = 200
            self.text = ""

        def json(self):
            return self._data

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params=None, headers=None):
            if url.endswith("/oauth/access_token"):
                return FakeResponse({"access_token": "facebook-access-token"})
            assert url == "https://graph.facebook.com/me"
            assert params["fields"] == "id,name,email,picture"
            return FakeResponse({"id": "12345", "name": "Facebook User"})

    monkeypatch.setattr(
        dang_nhap_xa_hoi_service,
        "cau_hinh_nha_cung_cap",
        lambda nha_cung_cap: {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "token_url": "https://graph.facebook.com/v22.0/oauth/access_token",
            "userinfo_url": "https://graph.facebook.com/me",
            "redirect_uri": "http://localhost:8000/api/v1/auth/facebook/callback",
        },
    )
    monkeypatch.setattr(dang_nhap_xa_hoi_service.httpx, "AsyncClient", lambda timeout: FakeClient())

    profile = asyncio.run(dang_nhap_xa_hoi_service.doi_ma_lay_ho_so("facebook", "facebook-code"))

    assert profile.email == "facebook_12345@sunlens.local"
    assert profile.nha_cung_cap_id == "12345"


def test_oauth_login_without_credentials_returns_frontend_error(client, monkeypatch):
    def fake_build_authorization_url(nha_cung_cap):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Đăng nhập Google chưa được cấu hình.",
        )

    monkeypatch.setattr("app.services.dang_nhap_xa_hoi_service.tao_url_uy_quyen", fake_build_authorization_url)
    response = client.get("/api/v1/auth/google/login", follow_redirects=False)
    assert response.status_code == 302, response.text
    fragment = parse_qs(urlparse(response.headers["location"]).fragment)
    assert fragment["nha_cung_cap"] == ["google"]
    assert fragment["oauth_error"] == ["Đăng nhập Google chưa được cấu hình."]


def test_forgot_password_sends_reset_email_when_email_exists(client, monkeypatch):
    email_da_gui: list[tuple[str, str, int]] = []

    def fake_gui_email_dat_lai_mat_khau(khach_hang, token):
        payload = decode_token(token, "reset_password")
        email_da_gui.append((khach_hang.thu_dien_tu, payload["sub"], len(payload["pwd"])))
        return True

    monkeypatch.setattr(
        "app.services.xac_thuc_service.gui_email_dat_lai_mat_khau",
        fake_gui_email_dat_lai_mat_khau,
    )

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "a@example.com"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Vui lòng kiểm tra email để đặt lại mật khẩu."
    assert email_da_gui == [("a@example.com", "3", 64)]


def test_forgot_password_returns_404_when_email_does_not_exist(client):
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "khong-ton-tai@example.com"},
    )

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Email không tồn tại trong hệ thống."


def test_forgot_password_returns_500_when_email_cannot_be_sent(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.xac_thuc_service.gui_email_dat_lai_mat_khau",
        lambda khach_hang, token: False,
    )

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "a@example.com"},
    )

    assert response.status_code == 500, response.text
    assert response.json()["detail"] == "Không thể gửi yêu cầu đặt lại mật khẩu."


def test_reset_password_success_allows_login_with_new_password(client):
    token = tao_token_dat_lai_mat_khau(client.customer_account)

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "mat_khau_moi": "654321"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Đặt lại mật khẩu thành công."

    old_login = client.post(
        "/api/v1/auth/login",
        json={"username": "kh01", "password": "123456"},
    )
    assert old_login.status_code == 401, old_login.text

    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "kh01", "password": "654321"},
    )
    assert new_login.status_code == 200, new_login.text


def test_reset_password_old_token_becomes_invalid_after_password_changes(client):
    token = tao_token_dat_lai_mat_khau(client.customer_account)

    first_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "mat_khau_moi": "654321"},
    )
    assert first_response.status_code == 200, first_response.text

    second_response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "mat_khau_moi": "987654"},
    )

    assert second_response.status_code == 400, second_response.text
    assert second_response.json()["detail"] == "Token đặt lại mật khẩu không còn hiệu lực."


def test_reset_password_rejects_invalid_token_type(client):
    token = create_token(
        subject="3",
        expires_delta=timedelta(minutes=5),
        token_type="access",
    )

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "mat_khau_moi": "654321"},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."


def test_reset_password_rejects_expired_token(client):
    settings = get_settings()
    token = create_token(
        subject="3",
        expires_delta=timedelta(minutes=-1),
        token_type="reset_password",
        extra_claims={"pwd": "x" * 64},
    )

    assert settings.reset_password_token_expire_minutes == 30

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "mat_khau_moi": "654321"},
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."
