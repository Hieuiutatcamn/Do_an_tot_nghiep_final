from tests.conftest import auth_headers


def test_customer_cart_crud_and_totals(client):
    headers = auth_headers(client)
    payload = {
        "Id_thiet_bi": 1,
        "so_luong": 2,
        "ngay_nhan": "2026-07-20",
        "ngay_tra": "2026-07-23",
    }

    create_response = client.post("/api/v1/cart", json=payload, headers=headers)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["Id_thiet_bi"] == 1
    assert created["so_ngay_thue"] == 3
    assert created["thanh_tien"] == 4_200_000

    cart_response = client.get("/api/v1/cart", headers=headers)
    assert cart_response.status_code == 200, cart_response.text
    cart = cart_response.json()
    assert cart["tong_san_pham"] == 2
    assert cart["tong_so_ngay_thue"] == 3
    assert cart["tong_tien_thue"] == 4_200_000

    item_id = created["Id_gio_hang"]
    update_response = client.put(
        f"/api/v1/cart/{item_id}",
        json={"so_luong": 1, "ngay_tra": "2026-07-24"},
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["so_luong"] == 1
    assert updated["so_ngay_thue"] == 4

    delete_response = client.delete(f"/api/v1/cart/{item_id}", headers=headers)
    assert delete_response.status_code == 204
    empty_cart = client.get("/api/v1/cart", headers=headers).json()
    assert empty_cart["items"] == []


def test_rental_from_cart_clears_cart_and_creates_notifications(client):
    customer_headers = auth_headers(client)
    admin_headers = auth_headers(client, "admin", "secret123")
    cart_payload = {
        "Id_thiet_bi": 1,
        "so_luong": 1,
        "ngay_nhan": "2026-07-20",
        "ngay_tra": "2026-07-23",
    }
    client.post("/api/v1/cart", json=cart_payload, headers=customer_headers)

    rental_response = client.post(
        "/api/v1/rentals",
        json={
            "danh_sach_thiet_bi": [
                {
                    "id_thiet_bi": 1,
                    "so_luong": 1,
                    "ngay_nhan": "2026-07-20T00:00:00",
                    "ngay_tra": "2026-07-23T00:00:00",
                }
            ]
        },
        headers=customer_headers,
    )
    assert rental_response.status_code == 201, rental_response.text

    cart_response = client.get("/api/v1/cart", headers=customer_headers)
    assert cart_response.json()["items"] == []

    user_notifications = client.get("/api/v1/notifications", headers=customer_headers)
    assert user_notifications.status_code == 200, user_notifications.text
    user_notification = user_notifications.json()[0]
    assert user_notification["loai_thong_bao"] == "Dat hang thanh cong"
    assert user_notification["tieu_de"] == "Đặt hàng thành công"
    assert user_notification["noi_dung"] == "Đơn thuê #1 đã được tạo thành công."
    assert user_notification["trang_thai"] == "Chua doc"
    assert "application/json; charset=utf-8" in user_notifications.headers["content-type"]

    unread_response = client.get("/api/v1/notifications/unread-count", headers=customer_headers)
    assert unread_response.json()["dem_thong_bao_chua_doc"] == 1

    read_response = client.put(
        f"/api/v1/notifications/{user_notification['Id_thong_bao']}/read",
        headers=customer_headers,
    )
    assert read_response.status_code == 200, read_response.text
    assert read_response.json()["trang_thai"] == "Da doc"

    admin_notifications = client.get("/api/v1/notifications", headers=admin_headers)
    assert admin_notifications.status_code == 200, admin_notifications.text
    assert admin_notifications.json()[0]["loai_thong_bao"] == "Co don hang moi"
    assert admin_notifications.json()[0]["tieu_de"] == "Có đơn hàng mới"
    assert admin_notifications.json()[0]["noi_dung"] == "Đơn thuê #1 vừa được tạo."
