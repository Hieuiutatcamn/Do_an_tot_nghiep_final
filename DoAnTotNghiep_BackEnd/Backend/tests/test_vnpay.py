from datetime import datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from app.services import thanh_toan_service
from app.services import het_han_thanh_toan_service
from app.services import gui_email_service
from tests.conftest import auth_headers


def _cau_hinh_vnpay():
    return SimpleNamespace(
        vnpay_tmn_code="VFY0ZGE8",
        vnpay_hash_secret="test-secret-123",
        vnpay_payment_url="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html",
        vnpay_return_url=(
            "http://127.0.0.1:5500/"
            "Webthuemayanh_FE/user/Sunlens_Camera/ket_qua_thanh_toan.html"
        ),
        vnpay_ipn_url="https://example.test/api/v1/thanh-toan/vnpay-ipn",
        vnpay_deposit_amount=200000,
        vnpay_payment_expire_minutes=15,
        vnpay_expiration_scan_seconds=30,
    )


def _tao_don(client, headers, phuong_thuc="VNPAY"):
    response = client.post(
        "/api/v1/rentals",
        json={
            "phuong_thuc_thanh_toan": phuong_thuc,
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
    assert response.status_code == 201, response.text
    return response.json()["id_don_thue"]


def _tao_url(client, headers, rental_id):
    response = client.post(
        "/api/v1/thanh-toan/vnpay-tao-url",
        json={
            "id_don_thue": rental_id,
            "so_tien": 200000,
            "noi_dung_thanh_toan": f"Thanh toán cọc đơn thuê DH{rental_id:04d}",
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["duong_dan_thanh_toan"]


def _params_tu_url(payment_url):
    return {
        key: values[0]
        for key, values in parse_qs(urlparse(payment_url).query).items()
    }


def _ky(params):
    signed = {
        key: value
        for key, value in params.items()
        if key != "vnp_SecureHash"
    }
    signed["vnp_SecureHash"] = thanh_toan_service.tao_chu_ky_vnpay(
        signed,
        _cau_hinh_vnpay().vnpay_hash_secret,
    )
    return signed


def test_vnpay_url_return_and_ipn_are_verified_and_idempotent(client, monkeypatch):
    monkeypatch.setattr(thanh_toan_service, "get_settings", _cau_hinh_vnpay)
    email_khach_hang: list[int] = []
    email_admin: list[int] = []
    monkeypatch.setattr(
        gui_email_service,
        "gui_email_thong_bao_dat_thue_cho_khach_hang",
        lambda don_thue, khach_hang, danh_sach_chi_tiet: (
            email_khach_hang.append(don_thue.id_don_thue) or True
        ),
    )
    monkeypatch.setattr(
        gui_email_service,
        "gui_email_thong_bao_don_thue_moi_cho_admin",
        lambda don_thue, khach_hang, danh_sach_chi_tiet: (
            email_admin.append(don_thue.id_don_thue) or True
        ),
    )
    headers = auth_headers(client)
    rental_id = _tao_don(client, headers)
    assert email_khach_hang == []
    assert email_admin == []
    payment_url = _tao_url(client, headers, rental_id)
    params = _params_tu_url(payment_url)
    secure_hash = params.pop("vnp_SecureHash")
    assert secure_hash == thanh_toan_service.tao_chu_ky_vnpay(
        params,
        _cau_hinh_vnpay().vnpay_hash_secret,
    )
    assert params["vnp_Amount"] == "20000000"
    assert params["vnp_ReturnUrl"] == _cau_hinh_vnpay().vnpay_return_url

    admin_headers = auth_headers(client, "admin", "secret123")
    admin_confirm = client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        json={"trang_thai": "Da xac nhan"},
        headers=admin_headers,
    )
    assert admin_confirm.status_code == 400

    callback = _ky(
        {
            "vnp_TmnCode": params["vnp_TmnCode"],
            "vnp_Amount": params["vnp_Amount"],
            "vnp_TxnRef": params["vnp_TxnRef"],
            "vnp_ResponseCode": "00",
            "vnp_TransactionStatus": "00",
            "vnp_TransactionNo": "14587421",
        }
    )
    return_response = client.get("/api/v1/thanh-toan/vnpay-return", params=callback)
    assert return_response.status_code == 200, return_response.text
    assert return_response.json()["thanh_cong"] is True
    assert return_response.json()["da_cap_nhat_he_thong"] is True
    assert return_response.json()["ngay_thanh_toan"]
    assert email_khach_hang == [rental_id]
    assert email_admin == [rental_id]

    ipn_response = client.get("/api/v1/thanh-toan/vnpay-ipn", params=callback)
    assert ipn_response.json()["RspCode"] == "02"
    assert email_khach_hang == [rental_id]
    assert email_admin == [rental_id]
    detail = client.get(f"/api/v1/rentals/{rental_id}", headers=headers).json()
    assert detail["trang_thai"] == "Da xac nhan"
    assert detail["phuong_thuc_thanh_toan"] == "VNPAY"
    assert detail["ma_giao_dich_vnpay"] == "14587421"
    assert float(detail["so_tien_da_thanh_toan"]) == 200000
    assert detail["ngay_thanh_toan"]
    assert "trang_thai_thanh_toan" not in detail

    repeated = client.get("/api/v1/thanh-toan/vnpay-ipn", params=callback)
    assert repeated.json()["RspCode"] == "02"
    assert email_khach_hang == [rental_id]
    assert email_admin == [rental_id]


def test_vnpay_rejects_bad_signature_amount_and_failed_transaction(client, monkeypatch):
    monkeypatch.setattr(thanh_toan_service, "get_settings", _cau_hinh_vnpay)
    headers = auth_headers(client)
    rental_id = _tao_don(client, headers)
    params = _params_tu_url(_tao_url(client, headers, rental_id))

    base_callback = {
        "vnp_TmnCode": params["vnp_TmnCode"],
        "vnp_Amount": params["vnp_Amount"],
        "vnp_TxnRef": params["vnp_TxnRef"],
        "vnp_ResponseCode": "00",
        "vnp_TransactionStatus": "00",
    }
    bad_signature = {**base_callback, "vnp_SecureHash": "invalid"}
    assert (
        client.get("/api/v1/thanh-toan/vnpay-ipn", params=bad_signature).json()[
            "RspCode"
        ]
        == "97"
    )

    wrong_amount = _ky({**base_callback, "vnp_Amount": "10000000"})
    assert (
        client.get("/api/v1/thanh-toan/vnpay-ipn", params=wrong_amount).json()[
            "RspCode"
        ]
        == "04"
    )

    failed = _ky(
        {
            **base_callback,
            "vnp_ResponseCode": "24",
            "vnp_TransactionStatus": "02",
        }
    )
    failed_response = client.get("/api/v1/thanh-toan/vnpay-ipn", params=failed)
    assert failed_response.json()["RspCode"] == "00"
    detail = client.get(f"/api/v1/rentals/{rental_id}", headers=headers).json()
    assert detail["trang_thai"] == "Cho thanh toan"
    assert float(detail["so_tien_da_thanh_toan"]) == 0
    assert "trang_thai_thanh_toan" not in detail


def test_manual_payment_image_keeps_pending_payment_state(client, monkeypatch):
    headers = auth_headers(client)
    rental_id = _tao_don(client, headers, "Chuyen khoan thu cong")

    async def fake_save_upload_file(upload_file, folder):
        return "/uploads/payment/chuyen-khoan.png"

    monkeypatch.setattr(
        "app.routers.don_thue.save_upload_file",
        fake_save_upload_file,
    )
    response = client.put(
        f"/api/v1/rentals/{rental_id}/payment-image",
        files={
            "anh_chuyen_khoan": (
                "chuyen-khoan.png",
                b"image",
                "image/png",
            )
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["trang_thai"] == "Da dat"
    assert data["phuong_thuc_thanh_toan"] == "Chuyen khoan thu cong"
    assert float(data["so_tien_da_thanh_toan"]) == 0
    assert "trang_thai_thanh_toan" not in data


def test_pending_vnpay_holds_inventory_then_expires_and_releases_it(client, monkeypatch):
    monkeypatch.setattr(thanh_toan_service, "get_settings", _cau_hinh_vnpay)
    headers = auth_headers(client)
    response = client.post(
        "/api/v1/rentals",
        json={
            "phuong_thuc_thanh_toan": "VNPAY",
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 2,
                }
            ],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    rental = response.json()
    assert rental["trang_thai"] == "Cho thanh toan"
    deadline = datetime.fromisoformat(rental["han_thanh_toan_vnpay"])

    held = client.get(
        "/api/v1/devices/1/availability",
        params={
            "ngay_nhan": "2026-07-20",
            "ngay_tra": "2026-07-21",
            "so_luong": 1,
        },
    )
    assert held.status_code == 200, held.text
    assert held.json()["so_luong_kha_dung"] == 0

    monkeypatch.setattr(
        het_han_thanh_toan_service,
        "thoi_gian_hien_tai",
        lambda: deadline + timedelta(seconds=1),
    )
    expired_detail = client.get(
        f"/api/v1/rentals/{rental['id_don_thue']}",
        headers=headers,
    )
    assert expired_detail.status_code == 200, expired_detail.text
    assert expired_detail.json()["trang_thai"] == "Da huy"

    released = client.get(
        "/api/v1/devices/1/availability",
        params={
            "ngay_nhan": "2026-07-20",
            "ngay_tra": "2026-07-21",
            "so_luong": 1,
        },
    )
    assert released.status_code == 200, released.text
    assert released.json()["so_luong_kha_dung"] == 2

    notification = client.get(
        "/api/v1/notifications",
        headers=headers,
    ).json()[0]
    assert notification["tieu_de"] == "Đơn VNPAY đã hết thời gian thanh toán"


def test_return_can_restore_auto_cancelled_order_when_pay_date_is_in_time(client, monkeypatch):
    monkeypatch.setattr(thanh_toan_service, "get_settings", _cau_hinh_vnpay)
    headers = auth_headers(client)
    rental_id = _tao_don(client, headers)
    params = _params_tu_url(_tao_url(client, headers, rental_id))
    deadline = datetime.strptime(params["vnp_ExpireDate"], "%Y%m%d%H%M%S")

    monkeypatch.setattr(
        het_han_thanh_toan_service,
        "thoi_gian_hien_tai",
        lambda: deadline + timedelta(seconds=1),
    )
    client.get(f"/api/v1/rentals/{rental_id}", headers=headers)

    callback = _ky(
        {
            "vnp_TmnCode": params["vnp_TmnCode"],
            "vnp_Amount": params["vnp_Amount"],
            "vnp_TxnRef": params["vnp_TxnRef"],
            "vnp_ResponseCode": "00",
            "vnp_TransactionStatus": "00",
            "vnp_TransactionNo": "15589741",
            "vnp_PayDate": (deadline - timedelta(seconds=1)).strftime("%Y%m%d%H%M%S"),
        }
    )
    response = client.get("/api/v1/thanh_toan/vnpay_return", params=callback)
    assert response.status_code == 200, response.text
    assert response.json()["thanh_cong"] is True
    detail = client.get(f"/api/v1/rentals/{rental_id}", headers=headers).json()
    assert detail["trang_thai"] == "Da xac nhan"
    assert detail["ma_giao_dich_vnpay"] == "15589741"


def test_return_rejects_payment_after_deadline(client, monkeypatch):
    monkeypatch.setattr(thanh_toan_service, "get_settings", _cau_hinh_vnpay)
    headers = auth_headers(client)
    rental_id = _tao_don(client, headers)
    params = _params_tu_url(_tao_url(client, headers, rental_id))
    deadline = datetime.strptime(params["vnp_ExpireDate"], "%Y%m%d%H%M%S")
    callback = _ky(
        {
            "vnp_TmnCode": params["vnp_TmnCode"],
            "vnp_Amount": params["vnp_Amount"],
            "vnp_TxnRef": params["vnp_TxnRef"],
            "vnp_ResponseCode": "00",
            "vnp_TransactionStatus": "00",
            "vnp_TransactionNo": "15589742",
            "vnp_PayDate": (deadline + timedelta(seconds=1)).strftime("%Y%m%d%H%M%S"),
        }
    )
    response = client.get("/api/v1/thanh-toan/vnpay-return", params=callback)
    assert response.status_code == 200, response.text
    assert response.json()["thanh_cong"] is False
    detail = client.get(f"/api/v1/rentals/{rental_id}", headers=headers).json()
    assert detail["trang_thai"] == "Cho thanh toan"
    assert detail["ma_giao_dich_vnpay"] is None


def test_vnpay_transaction_reference_variants():
    assert thanh_toan_service._lay_id_don_thue("DH44_20260619121557") == 44
    assert thanh_toan_service._lay_id_don_thue("DH0044_20260619121557123456") == 44
    assert thanh_toan_service._lay_id_don_thue("44_20260619121557") == 44
