from tests.conftest import auth_headers


def test_create_rental_calculates_total_and_blocks_insufficient_stock(client):
    headers = auth_headers(client)
    payload = {
        "ghi_chu": "Thue test",
        "danh_sach_thiet_bi": [
            {
                "id_thiet_bi": 1,
                "ngay_nhan": "2026-07-20T08:00:00",
                "ngay_tra": "2026-07-22T08:00:00",
                "so_luong": 1,
            }
        ],
    }
    response = client.post("/api/v1/rentals", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["trang_thai"] == "Da dat"
    assert float(data["tong_tien"]) == 1400000
    assert data["details"][0]["gia_thue"] == "700000.00" or float(data["details"][0]["gia_thue"]) == 700000
    assert data["details"][0]["trang_thai"] == "Da dat"
    assert data["khach_hang"]["ho_ten"] == "Nguyen Van A"
    assert "anh_cccd_mat_truoc" in data
    assert "anh_cccd_mat_sau" in data

    insufficient_payload = {
        "items": [
            {
                "id_thiet_bi": 2,
                "ngay_nhan": "2026-07-20T08:00:00",
                "ngay_tra": "2026-07-21T08:00:00",
                "so_luong": 1,
            }
        ],
    }
    insufficient_response = client.post("/api/v1/rentals", json=insufficient_payload, headers=headers)
    assert insufficient_response.status_code == 400
    list_response = client.get("/api/v1/rentals", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] == 1


def test_rental_detail_returns_customer_identity_images(client):
    headers = auth_headers(client)
    profile_response = client.put(
        "/api/v1/users/me",
        json={
            "anh_cccd_mat_truoc": "/uploads/cccd/mat-truoc.jpg",
            "anh_cccd_mat_sau": "/uploads/cccd/mat-sau.jpg",
            "dia_chi": "382 Hùng Vương, Đà Nẵng",
            "so_cccd": "048123456789",
        },
        headers=headers,
    )
    assert profile_response.status_code == 200, profile_response.text

    create_response = client.post(
        "/api/v1/rentals",
        json={
            "danh_sach_thiet_bi": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text

    detail_response = client.get(
        f"/api/v1/rentals/{create_response.json()['id_don_thue']}",
        headers=headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["anh_cccd_mat_truoc"] == "/uploads/cccd/mat-truoc.jpg"
    assert detail["anh_cccd_mat_sau"] == "/uploads/cccd/mat-sau.jpg"
    assert detail["khach_hang"]["anh_cccd_mat_truoc"] == "/uploads/cccd/mat-truoc.jpg"
    assert detail["khach_hang"]["anh_cccd_mat_sau"] == "/uploads/cccd/mat-sau.jpg"
    assert detail["khach_hang"]["dia_chi"] == "382 Hùng Vương, Đà Nẵng"
    assert detail["khach_hang"]["so_cccd"] == "048123456789"
    assert detail["khach_hang"]["email"] == "a@example.com"


def test_rental_cors_preflight_and_payment_image(client, monkeypatch):
    preflight_response = client.options(
        "/api/v1/rentals",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert preflight_response.status_code == 200, preflight_response.text
    assert preflight_response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"

    headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "danh_sach_thiet_bi": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    rental_id = create_response.json()["id_don_thue"]

    async def fake_save_upload_file(upload_file, folder):
        assert upload_file.filename == "chuyen-khoan.png"
        assert folder == "payment"
        return "/uploads/payment/chuyen-khoan.png"

    monkeypatch.setattr("app.routers.don_thue.save_upload_file", fake_save_upload_file)
    upload_response = client.put(
        f"/api/v1/rentals/{rental_id}/payment-image",
        files={"anh_chuyen_khoan": ("chuyen-khoan.png", b"image", "image/png")},
        headers=headers,
    )
    assert upload_response.status_code == 200, upload_response.text
    assert upload_response.json()["anh_chuyen_khoan"] == "/uploads/payment/chuyen-khoan.png"


def test_unhandled_rental_error_returns_cors_json(client, monkeypatch):
    def raise_unhandled_error(*args, **kwargs):
        raise RuntimeError("Lỗi kiểm thử")

    monkeypatch.setattr(
        "app.services.don_thue_service.tao_don_thue",
        raise_unhandled_error,
    )
    response = client.post(
        "/api/v1/rentals",
        json={
            "danh_sach_thiet_bi": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers={
            **auth_headers(client),
            "Origin": "http://127.0.0.1:5500",
        },
    )
    assert response.status_code == 500, response.text
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
    assert response.json()["detail"].startswith("Lỗi máy chủ khi xử lý yêu cầu")


def test_staff_can_update_rental_status(client):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=customer_headers,
    )
    assert create_response.status_code == 201, create_response.text
    rental_id = create_response.json()["id_don_thue"]

    admin_headers = auth_headers(client, "admin", "secret123")
    transitions = (
        ("Da xac nhan", "Xác nhận đơn thuê", f"Đơn thuê #{rental_id} đã được xác nhận."),
        ("Dang thue", None, None),
        ("Da qua han", "Đơn thuê quá hạn", f"Đơn thuê #{rental_id} đã quá hạn."),
        ("Da thue", "Đơn thuê hoàn tất", f"Đơn thuê #{rental_id} đã hoàn tất."),
    )
    for rental_status, title, content in transitions:
        status_response = client.patch(
            f"/api/v1/rentals/{rental_id}/status",
            json={"trang_thai": rental_status},
            headers=admin_headers,
        )
        assert status_response.status_code == 200, status_response.text
        assert status_response.json()["trang_thai"] == rental_status
        assert all(
            chi_tiet["trang_thai"] == rental_status
            for chi_tiet in status_response.json()["details"]
        )
        if rental_status == "Da xac nhan":
            assert status_response.json()["phuong_thuc_thanh_toan"] == "Chuyen khoan thu cong"
            assert float(status_response.json()["so_tien_da_thanh_toan"]) == 200000

        if not title:
            continue
        notifications_response = client.get("/api/v1/notifications", headers=customer_headers)
        notification = notifications_response.json()[0]
        assert notification["tieu_de"] == title
        assert notification["noi_dung"] == content

    invalid_transition = client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        json={"trang_thai": "Da dat"},
        headers=admin_headers,
    )
    assert invalid_transition.status_code == 400

    detail_response = client.get(
        f"/api/v1/rentals/{rental_id}",
        headers=customer_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    assert float(detail_response.json()["so_tien_da_thanh_toan"]) == 200000
    assert all(
        chi_tiet["trang_thai"] == "Da thue"
        for chi_tiet in detail_response.json()["details"]
    )


def test_cap_nhat_trang_thai_chi_tiet_don_thue_dong_bo_nguoc_len_don_tong(client):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                },
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-21T08:00:00",
                    "ngay_tra": "2026-07-22T08:00:00",
                    "so_luong": 1,
                },
            ]
        },
        headers=customer_headers,
    )
    assert create_response.status_code == 201, create_response.text
    rental = create_response.json()
    rental_id = rental["id_don_thue"]
    detail_ids = [item["id_chi_tiet_don_thue"] for item in rental["details"]]

    employee_headers = auth_headers(client, "nhanvien", "secret123")
    first_update = client.patch(
        f"/api/v1/chi-tiet-don-hang/{detail_ids[0]}/trang-thai",
        json={"trang_thai": "Da xac nhan"},
        headers=employee_headers,
    )
    assert first_update.status_code == 200, first_update.text
    assert first_update.json()["trang_thai"] == "Da xac nhan"

    rental_after_first_update = client.get(
        f"/api/v1/rentals/{rental_id}",
        headers=employee_headers,
    )
    assert rental_after_first_update.status_code == 200, rental_after_first_update.text
    assert rental_after_first_update.json()["trang_thai"] == "Da dat"
    assert [item["trang_thai"] for item in rental_after_first_update.json()["details"]] == [
        "Da xac nhan",
        "Da dat",
    ]

    second_update = client.patch(
        f"/api/v1/chi-tiet-don-hang/{detail_ids[1]}/trang-thai",
        json={"trang_thai": "Da xac nhan"},
        headers=employee_headers,
    )
    assert second_update.status_code == 200, second_update.text
    assert second_update.json()["trang_thai"] == "Da xac nhan"

    rental_after_second_update = client.get(
        f"/api/v1/rentals/{rental_id}",
        headers=employee_headers,
    )
    assert rental_after_second_update.status_code == 200, rental_after_second_update.text
    assert rental_after_second_update.json()["trang_thai"] == "Da xac nhan"
    assert float(rental_after_second_update.json()["so_tien_da_thanh_toan"]) == 200000
    assert all(
        item["trang_thai"] == "Da xac nhan"
        for item in rental_after_second_update.json()["details"]
    )

    third_update = client.patch(
        f"/api/v1/chi-tiet-don-hang/{detail_ids[0]}/trang-thai",
        json={"trang_thai": "Dang thue"},
        headers=employee_headers,
    )
    assert third_update.status_code == 200, third_update.text
    assert third_update.json()["trang_thai"] == "Dang thue"

    rental_after_third_update = client.get(
        f"/api/v1/rentals/{rental_id}",
        headers=employee_headers,
    )
    assert rental_after_third_update.status_code == 200, rental_after_third_update.text
    assert rental_after_third_update.json()["trang_thai"] == "Da xac nhan"
    assert [item["trang_thai"] for item in rental_after_third_update.json()["details"]] == [
        "Dang thue",
        "Da xac nhan",
    ]

    customer_forbidden = client.patch(
        f"/api/v1/chi-tiet-don-hang/{detail_ids[1]}/trang-thai",
        json={"trang_thai": "Dang thue"},
        headers=customer_headers,
    )
    assert customer_forbidden.status_code == 403, customer_forbidden.text

    final_update = client.patch(
        f"/api/v1/chi-tiet-don-hang/{detail_ids[1]}/trang-thai",
        json={"trang_thai": "Dang thue"},
        headers=employee_headers,
    )
    assert final_update.status_code == 200, final_update.text
    assert final_update.json()["trang_thai"] == "Dang thue"

    chi_tiet_don_hang_response = client.get(
        f"/api/v1/chi-tiet-don-hang?order_id={rental_id}",
        headers=employee_headers,
    )
    assert chi_tiet_don_hang_response.status_code == 200, chi_tiet_don_hang_response.text
    assert all(
        item["trang_thai"] == "Dang thue"
        for item in chi_tiet_don_hang_response.json()
    )

    legacy_chi_tiet_response = client.get(
        f"/api/v1/order-details?order_id={rental_id}",
        headers=employee_headers,
    )
    assert legacy_chi_tiet_response.status_code == 200, legacy_chi_tiet_response.text
    assert all(
        item["trang_thai"] == "Dang thue"
        for item in legacy_chi_tiet_response.json()
    )

    rental_after_final_update = client.get(
        f"/api/v1/rentals/{rental_id}",
        headers=employee_headers,
    )
    assert rental_after_final_update.status_code == 200, rental_after_final_update.text
    assert rental_after_final_update.json()["trang_thai"] == "Dang thue"
    assert all(
        item["trang_thai"] == "Dang thue"
        for item in rental_after_final_update.json()["details"]
    )


def test_manual_deposit_update_is_idempotent_and_does_not_change_vnpay():
    from decimal import Decimal

    from app.models.don_thue import DonThue
    from app.services.don_thue_service import cap_nhat_so_tien_da_thanh_toan_thu_cong

    manual_rental = DonThue(
        phuong_thuc_thanh_toan="Chuyen khoan thu cong",
        so_tien_da_thanh_toan=Decimal("100000"),
    )
    cap_nhat_so_tien_da_thanh_toan_thu_cong(manual_rental)
    cap_nhat_so_tien_da_thanh_toan_thu_cong(manual_rental)
    assert manual_rental.phuong_thuc_thanh_toan == "Chuyen khoan thu cong"
    assert manual_rental.so_tien_da_thanh_toan == Decimal("200000")

    manual_rental.so_tien_da_thanh_toan = Decimal("250000")
    cap_nhat_so_tien_da_thanh_toan_thu_cong(manual_rental)
    assert manual_rental.so_tien_da_thanh_toan == Decimal("250000")

    vnpay_rental = DonThue(
        phuong_thuc_thanh_toan="VNPAY",
        so_tien_da_thanh_toan=Decimal("175000"),
        ma_giao_dich_vnpay="15589741",
    )
    cap_nhat_so_tien_da_thanh_toan_thu_cong(vnpay_rental)
    assert vnpay_rental.phuong_thuc_thanh_toan == "VNPAY"
    assert vnpay_rental.so_tien_da_thanh_toan == Decimal("175000")
    assert vnpay_rental.ma_giao_dich_vnpay == "15589741"


def test_customer_cancel_creates_vietnamese_notification(client):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=customer_headers,
    )
    rental_id = create_response.json()["id_don_thue"]

    cancel_response = client.patch(
        f"/api/v1/rentals/{rental_id}/cancel",
        json={"ly_do_huy": "Thay đổi kế hoạch"},
        headers=customer_headers,
    )
    assert cancel_response.status_code == 200, cancel_response.text

    notification = client.get("/api/v1/notifications", headers=customer_headers).json()[0]
    assert notification["tieu_de"] == "Hủy đơn hàng thành công"
    assert notification["noi_dung"] == f"Bạn đã hủy đơn hàng #{rental_id} thành công."


def test_customer_updates_pending_rental_information_without_changing_dates_or_old_image(client):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "ghi_chu": "Ghi chú cũ",
            "anh_chuyen_khoan": "/uploads/payment/anh-cu.png",
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-22T08:00:00",
                    "so_luong": 1,
                }
            ],
        },
        headers=customer_headers,
    )
    assert create_response.status_code == 201, create_response.text
    rental_id = create_response.json()["id_don_thue"]
    original_detail = create_response.json()["details"][0]

    update_response = client.put(
        f"/api/v1/rentals/{rental_id}/khach_hang_update",
        data={
            "ho_ten": "  Nguyễn Văn Cập Nhật  ",
            "sdt": " 0987654321 ",
            "dia_chi": "  123 Đường Mới, Đà Nẵng ",
            "ghi_chu": "Giao máy buổi sáng",
        },
        headers=customer_headers,
    )
    assert update_response.status_code == 200, update_response.text
    data = update_response.json()
    assert data["khach_hang"]["ho_ten"] == "Nguyễn Văn Cập Nhật"
    assert data["khach_hang"]["sdt"] == "0987654321"
    assert data["khach_hang"]["dia_chi"] == "123 Đường Mới, Đà Nẵng"
    assert data["ghi_chu"] == "Giao máy buổi sáng"
    assert data["anh_chuyen_khoan"] == "/uploads/payment/anh-cu.png"
    assert data["details"][0]["ngay_nhan"] == original_detail["ngay_nhan"]
    assert data["details"][0]["ngay_tra"] == original_detail["ngay_tra"]


def test_customer_updates_pending_rental_with_payment_image_alias(client, monkeypatch):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=customer_headers,
    )
    rental_id = create_response.json()["id_don_thue"]

    async def fake_save_upload_file(upload_file, folder):
        assert upload_file.filename == "anh-moi.webp"
        assert folder == "payment"
        return "/uploads/payment/anh-moi.webp"

    monkeypatch.setattr("app.routers.don_thue.save_upload_file", fake_save_upload_file)
    update_response = client.put(
        f"/api/v1/rentals/{rental_id}/khach_hang_update",
        data={
            "ho_ten": "Nguyen Van A",
            "sdt": "0911111111",
            "dia_chi": "Đà Nẵng",
            "ghi_chu": "",
        },
        files={"Anh_chuyen_khoan": ("anh-moi.webp", b"image", "image/webp")},
        headers=customer_headers,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["anh_chuyen_khoan"] == "/uploads/payment/anh-moi.webp"


def test_customer_update_validates_required_fields_and_payment_image_type(client):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=customer_headers,
    )
    rental_id = create_response.json()["id_don_thue"]

    empty_name_response = client.put(
        f"/api/v1/rentals/{rental_id}/khach_hang_update",
        data={
            "ho_ten": "   ",
            "sdt": "0911111111",
            "dia_chi": "Đà Nẵng",
        },
        headers=customer_headers,
    )
    assert empty_name_response.status_code == 400, empty_name_response.text
    assert empty_name_response.json()["detail"] == "Họ tên không được trống."

    invalid_image_response = client.put(
        f"/api/v1/rentals/{rental_id}/khach_hang_update",
        data={
            "ho_ten": "Nguyen Van A",
            "sdt": "0911111111",
            "dia_chi": "Đà Nẵng",
        },
        files={"anh_chuyen_khoan": ("anh.gif", b"gif", "image/gif")},
        headers=customer_headers,
    )
    assert invalid_image_response.status_code == 400, invalid_image_response.text
    assert invalid_image_response.json()["detail"] == "Vui lòng chọn file ảnh hợp lệ dưới 5MB."


def test_customer_cannot_update_non_pending_or_another_customers_rental(client, monkeypatch):
    owner_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/rentals",
        json={
            "items": [
                {
                    "id_thiet_bi": 1,
                    "ngay_nhan": "2026-07-20T08:00:00",
                    "ngay_tra": "2026-07-21T08:00:00",
                    "so_luong": 1,
                }
            ]
        },
        headers=owner_headers,
    )
    rental_id = create_response.json()["id_don_thue"]

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "kh02",
            "password": "123456",
            "ho_ten": "Khách Hàng Khác",
            "sdt": "0912222222",
            "email": "khac@example.com",
        },
    )
    assert register_response.status_code == 201, register_response.text
    other_headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}
    forbidden_response = client.put(
        f"/api/v1/rentals/{rental_id}/khach_hang_update",
        data={
            "ho_ten": "Khách Hàng Khác",
            "sdt": "0912222222",
            "dia_chi": "Huế",
        },
        headers=other_headers,
    )
    assert forbidden_response.status_code == 403, forbidden_response.text

    admin_headers = auth_headers(client, "admin", "secret123")
    status_response = client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        json={"trang_thai": "Da xac nhan"},
        headers=admin_headers,
    )
    assert status_response.status_code == 200, status_response.text

    blocked_response = client.put(
        f"/api/v1/rentals/{rental_id}/khach_hang_update",
        data={
            "ho_ten": "Nguyen Van A",
            "sdt": "0911111111",
            "dia_chi": "Đà Nẵng",
        },
        headers=owner_headers,
    )
    assert blocked_response.status_code == 400, blocked_response.text
    assert blocked_response.json()["detail"] == "Chỉ được cập nhật đơn thuê đang chờ xác nhận."

    async def should_not_save(*args, **kwargs):
        raise AssertionError("Không được lưu ảnh khi đơn không còn chờ xác nhận")

    monkeypatch.setattr("app.routers.don_thue.save_upload_file", should_not_save)
    blocked_image_response = client.put(
        f"/api/v1/rentals/{rental_id}/payment-image",
        files={"anh_chuyen_khoan": ("anh-moi.png", b"image", "image/png")},
        headers=owner_headers,
    )
    assert blocked_image_response.status_code == 400, blocked_image_response.text
    assert blocked_image_response.json()["detail"] == "Chỉ được cập nhật đơn thuê đang chờ xác nhận."
