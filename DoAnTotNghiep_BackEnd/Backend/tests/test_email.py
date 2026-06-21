from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.routers import email as email_router
from app.services import gui_email_service
from tests.conftest import auth_headers


def _du_lieu_email_mau():
    thiet_bi = SimpleNamespace(ten_thiet_bi="<Sony A7III>")
    chi_tiet = SimpleNamespace(
        id_thiet_bi=1,
        device=thiet_bi,
        ngay_nhan=datetime(2026, 7, 20, 8, 0),
        ngay_tra=datetime(2026, 7, 21, 8, 0),
        so_luong=2,
        gia_thue=Decimal("700000"),
    )
    don_thue = SimpleNamespace(
        id_don_thue=12,
        ngay_dat=datetime(2026, 6, 19, 9, 30),
        trang_thai="Da xac nhan",
        tong_tien=Decimal("1400000"),
        so_tien_da_thanh_toan=Decimal("200000"),
        phuong_thuc_thanh_toan="VNPAY",
    )
    khach_hang = SimpleNamespace(
        ho_ten="<Nguyễn Văn A>",
        sdt="0911111111",
        email="a@example.com",
        dia_chi="Đà Nẵng",
    )
    return don_thue, khach_hang, [chi_tiet]


def _tao_don_thu_cong(client, headers):
    return client.post(
        "/api/v1/rentals",
        json={
            "phuong_thuc_thanh_toan": "Chuyen khoan thu cong",
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ],
        },
        headers=headers,
    )


def test_noi_dung_email_html_tieng_viet_va_escape_du_lieu():
    don_thue, khach_hang, chi_tiet = _du_lieu_email_mau()

    html_khach = gui_email_service.tao_noi_dung_email_dat_thue_cho_khach_hang(
        don_thue,
        khach_hang,
        chi_tiet,
    )
    html_admin = gui_email_service.tao_noi_dung_email_don_thue_moi_cho_admin(
        don_thue,
        khach_hang,
        chi_tiet,
    )
    html_xac_nhan = (
        gui_email_service.tao_noi_dung_email_don_thue_da_xac_nhan_cho_khach_hang(
            don_thue,
            khach_hang,
            chi_tiet,
        )
    )

    assert "DH12" in html_khach
    assert "20/07/2026 08:00" in html_khach
    assert "1.400.000 đ" in html_khach
    assert "Đã xác nhận" in html_khach
    assert "&lt;Nguyễn Văn A&gt;" in html_khach
    assert "&lt;Sony A7III&gt;" in html_admin
    assert "<Nguyễn Văn A>" not in html_khach
    assert "382 Hùng Vương, Thanh Khê, Đà Nẵng" in html_xac_nhan
    assert "0906 586 982" in html_xac_nhan


def test_gui_email_thieu_api_key_khong_phat_sinh_loi(monkeypatch):
    monkeypatch.setattr(
        gui_email_service,
        "get_settings",
        lambda: SimpleNamespace(
            resend_api_key="",
            email_from="SunLens Camera <onboarding@resend.dev>",
            email_admin="admin@example.com",
        ),
    )
    assert gui_email_service.gui_email(
        "admin@example.com",
        "Kiểm thử",
        "<p>Nội dung</p>",
    ) is False


def test_resend_sandbox_chuyen_email_khach_ve_email_kiem_thu(
    monkeypatch,
    gia_lap_resend,
):
    payloads: list[dict] = []
    monkeypatch.setattr(
        gia_lap_resend.Emails,
        "send",
        lambda params: payloads.append(params) or {"id": "email_kiem_thu"},
    )
    monkeypatch.setattr(
        gui_email_service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="development",
            resend_api_key="re_test",
            email_from="SunLens Camera <onboarding@resend.dev>",
            email_admin="owner@example.com",
            resend_test_recipient="",
        ),
    )

    assert gui_email_service.gui_email(
        "customer@yahoo.com",
        "Thông báo đơn thuê",
        "<p>Nội dung</p>",
    )
    assert payloads[0]["to"] == ["owner@example.com"]
    assert payloads[0]["subject"].startswith("[TEST cho cu***@yahoo.com]")
    assert "Môi trường thử nghiệm Resend" in payloads[0]["html"]


def test_resend_sandbox_khong_chuyen_email_trong_production(
    monkeypatch,
    gia_lap_resend,
):
    da_gui: list[dict] = []
    monkeypatch.setattr(
        gia_lap_resend.Emails,
        "send",
        lambda params: da_gui.append(params) or {"id": "khong_duoc_gui"},
    )
    monkeypatch.setattr(
        gui_email_service,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="production",
            resend_api_key="re_test",
            email_from="SunLens Camera <onboarding@resend.dev>",
            email_admin="owner@example.com",
            resend_test_recipient="",
        ),
    )

    assert gui_email_service.gui_email(
        "customer@yahoo.com",
        "Thông báo đơn thuê",
        "<p>Nội dung</p>",
    ) is False
    assert da_gui == []


def test_khach_khong_co_email_van_gui_cho_admin(monkeypatch):
    don_thue, khach_hang, chi_tiet = _du_lieu_email_mau()
    khach_hang.email = ""
    da_gui: list[tuple[str, str]] = []
    monkeypatch.setattr(
        gui_email_service,
        "get_settings",
        lambda: SimpleNamespace(email_admin="admin@example.com"),
    )
    monkeypatch.setattr(
        gui_email_service,
        "gui_email",
        lambda nguoi_nhan, tieu_de, noi_dung_html: (
            da_gui.append((nguoi_nhan, tieu_de)) or True
        ),
    )

    assert (
        gui_email_service.gui_email_thong_bao_dat_thue_cho_khach_hang(
            don_thue,
            khach_hang,
            chi_tiet,
        )
        is False
    )
    assert gui_email_service.gui_email_thong_bao_don_thue_moi_cho_admin(
        don_thue,
        khach_hang,
        chi_tiet,
    )
    assert da_gui == [
        ("admin@example.com", "SunLens Camera - Có đơn thuê mới DH12")
    ]


def test_endpoint_email_test_chi_admin_duoc_goi(client, monkeypatch):
    da_gui: list[str] = []
    monkeypatch.setattr(
        gui_email_service,
        "gui_email",
        lambda nguoi_nhan, tieu_de, noi_dung_html: (
            da_gui.append(nguoi_nhan) or True
        ),
    )

    customer_response = client.get(
        "/api/v1/email/test",
        headers=auth_headers(client),
    )
    assert customer_response.status_code == 403

    admin_response = client.get(
        "/api/v1/email/test",
        headers=auth_headers(client, "admin", "secret123"),
    )
    assert admin_response.status_code == 200, admin_response.text
    assert admin_response.json() == {
        "message": "Đã gửi email test.",
        "ma_email_resend": None,
    }
    assert da_gui


def test_endpoint_email_test_bao_ro_khi_thieu_cau_hinh(client, monkeypatch):
    monkeypatch.setattr(
        email_router,
        "get_settings",
        lambda: SimpleNamespace(
            resend_api_key="",
            email_from="SunLens Camera <onboarding@resend.dev>",
            email_admin="admin@example.com",
        ),
    )
    response = client.get(
        "/api/v1/email/test",
        headers=auth_headers(client, "admin", "secret123"),
    )
    assert response.status_code == 503
    assert response.json()["detail"] == (
        "RESEND_API_KEY chưa được cấu hình trên máy chủ."
    )


def test_don_thu_cong_gui_email_khach_va_admin_sau_khi_tao(client, monkeypatch):
    da_gui_khach: list[int] = []
    da_gui_admin: list[int] = []
    monkeypatch.setattr(
        gui_email_service,
        "gui_email_thong_bao_dat_thue_cho_khach_hang",
        lambda don_thue, khach_hang, danh_sach_chi_tiet: (
            da_gui_khach.append(don_thue.id_don_thue) or True
        ),
    )
    monkeypatch.setattr(
        gui_email_service,
        "gui_email_thong_bao_don_thue_moi_cho_admin",
        lambda don_thue, khach_hang, danh_sach_chi_tiet: (
            da_gui_admin.append(don_thue.id_don_thue) or True
        ),
    )

    response = _tao_don_thu_cong(client, auth_headers(client))

    assert response.status_code == 201, response.text
    assert response.json()["trang_thai"] == "Da dat"
    assert da_gui_khach == [response.json()["id_don_thue"]]
    assert da_gui_admin == [response.json()["id_don_thue"]]


def test_resend_loi_khong_rollback_don_thu_cong(client, monkeypatch, gia_lap_resend):
    def resend_bi_loi(params):
        raise RuntimeError("Resend tạm thời không khả dụng")

    monkeypatch.setattr(gia_lap_resend.Emails, "send", resend_bi_loi)
    response = _tao_don_thu_cong(client, auth_headers(client))

    assert response.status_code == 201, response.text
    assert response.json()["trang_thai"] == "Da dat"


def test_thieu_thu_vien_resend_khong_lam_sap_backend(client, monkeypatch):
    monkeypatch.setattr(
        gui_email_service,
        "nap_thu_vien_resend",
        lambda: None,
    )

    response = client.get("/")
    assert response.status_code == 200
    assert gui_email_service.gui_email(
        "admin@example.com",
        "Kiểm thử",
        "<p>Nội dung</p>",
    ) is False


def test_endpoint_email_bao_ro_khi_thieu_thu_vien(client, monkeypatch):
    monkeypatch.setattr(
        gui_email_service,
        "nap_thu_vien_resend",
        lambda: None,
    )

    response = client.get(
        "/api/v1/email/test",
        headers=auth_headers(client, "admin", "secret123"),
    )

    assert response.status_code == 503
    assert "Chưa cài thư viện resend" in response.json()["detail"]


def test_loi_dung_html_khong_rollback_don_thu_cong(client, monkeypatch):
    monkeypatch.setattr(
        gui_email_service,
        "tao_noi_dung_email_dat_thue_cho_khach_hang",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("Không thể dựng HTML")
        ),
    )
    response = _tao_don_thu_cong(client, auth_headers(client))

    assert response.status_code == 201, response.text
    assert response.json()["trang_thai"] == "Da dat"


def test_admin_xac_nhan_don_gui_email_xac_nhan_cho_khach(client, monkeypatch):
    da_gui_xac_nhan: list[int] = []
    monkeypatch.setattr(
        gui_email_service,
        "gui_email_thong_bao_don_thue_da_xac_nhan_cho_khach_hang",
        lambda don_thue, khach_hang, danh_sach_chi_tiet: (
            da_gui_xac_nhan.append(don_thue.id_don_thue) or True
        ),
    )
    don_response = _tao_don_thu_cong(client, auth_headers(client))
    assert don_response.status_code == 201, don_response.text
    id_don_thue = don_response.json()["id_don_thue"]

    response = client.patch(
        f"/api/v1/rentals/{id_don_thue}/status",
        json={"trang_thai": "Da xac nhan"},
        headers=auth_headers(client, "admin", "secret123"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["trang_thai"] == "Da xac nhan"
    assert da_gui_xac_nhan == [id_don_thue]
