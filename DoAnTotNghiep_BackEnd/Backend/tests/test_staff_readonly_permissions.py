from tests.conftest import auth_headers


THONG_BAO_CAM_QUYEN = "Bạn không có quyền thực hiện thao tác này."


def test_nhan_vien_duoc_xem_san_pham_danh_muc_va_ma_giam_gia(client):
    admin_headers = auth_headers(client, "admin", "secret123")
    employee_headers = auth_headers(client, "nhanvien", "secret123")

    tao_ma_response = client.post(
        "/api/v1/admin/discounts",
        json={
            "ma_code": "NVREADONLY",
            "ten_ma": "Mã chỉ đọc",
            "loai_giam_gia": "phan_tram",
            "gia_tri_giam": 10,
            "dieu_kien_loai": "khong_dieu_kien",
            "so_luong": 5,
            "trang_thai": "dang_hoat_dong",
        },
        headers=admin_headers,
    )
    assert tao_ma_response.status_code == 201, tao_ma_response.text

    response_devices = client.get("/api/v1/devices", headers=employee_headers)
    assert response_devices.status_code == 200, response_devices.text
    assert response_devices.json()["total"] >= 1

    response_device_detail = client.get("/api/v1/devices/1", headers=employee_headers)
    assert response_device_detail.status_code == 200, response_device_detail.text

    response_categories = client.get("/api/v1/categories", headers=employee_headers)
    assert response_categories.status_code == 200, response_categories.text
    assert response_categories.json()["total"] >= 1

    response_category_detail = client.get("/api/v1/categories/1", headers=employee_headers)
    assert response_category_detail.status_code == 200, response_category_detail.text

    response_discounts = client.get("/api/v1/admin/discounts", headers=employee_headers)
    assert response_discounts.status_code == 200, response_discounts.text
    assert response_discounts.json()["total"] >= 1


def test_nhan_vien_bi_chan_cac_thao_tac_ghi(client):
    admin_headers = auth_headers(client, "admin", "secret123")
    employee_headers = auth_headers(client, "nhanvien", "secret123")

    tao_ma_response = client.post(
        "/api/v1/admin/discounts",
        json={
            "ma_code": "ONLYADMIN",
            "ten_ma": "Chỉ admin",
            "loai_giam_gia": "phan_tram",
            "gia_tri_giam": 15,
            "dieu_kien_loai": "khong_dieu_kien",
            "so_luong": 10,
            "trang_thai": "dang_hoat_dong",
        },
        headers=admin_headers,
    )
    assert tao_ma_response.status_code == 201, tao_ma_response.text
    discount_id = tao_ma_response.json()["id_ma_giam_gia"]

    cac_phan_hoi = [
        client.post(
            "/api/v1/devices",
            json={
                "ten_thiet_bi": "Fujifilm X-T5",
                "id_danh_muc": 1,
                "gia_thue": 500000,
                "so_luong": 1,
                "tinh_trang": "San sang",
            },
            headers=employee_headers,
        ),
        client.put(
            "/api/v1/devices/1",
            json={"ten_thiet_bi": "Sony A7III Updated"},
            headers=employee_headers,
        ),
        client.delete("/api/v1/devices/1", headers=employee_headers),
        client.post(
            "/api/v1/categories",
            json={"ten_danh_muc": "Phụ kiện", "mo_ta": "Danh mục mới"},
            headers=employee_headers,
        ),
        client.put(
            "/api/v1/categories/1",
            json={"ten_danh_muc": "Máy ảnh"},
            headers=employee_headers,
        ),
        client.delete("/api/v1/categories/1", headers=employee_headers),
        client.post(
            "/api/v1/admin/discounts",
            json={
                "ma_code": "FORBIDDEN",
                "ten_ma": "Không được tạo",
                "loai_giam_gia": "tien_mat",
                "gia_tri_giam": 100000,
                "dieu_kien_loai": "khong_dieu_kien",
                "so_luong": 1,
                "trang_thai": "dang_hoat_dong",
            },
            headers=employee_headers,
        ),
        client.put(
            f"/api/v1/admin/discounts/{discount_id}",
            json={"ten_ma": "Bị chặn"},
            headers=employee_headers,
        ),
        client.patch(
            f"/api/v1/admin/discounts/{discount_id}/status",
            json={"trang_thai": "tam_ngung"},
            headers=employee_headers,
        ),
        client.delete(f"/api/v1/admin/discounts/{discount_id}", headers=employee_headers),
    ]

    for response in cac_phan_hoi:
        assert response.status_code == 403, response.text
        assert response.json()["detail"] == THONG_BAO_CAM_QUYEN


def test_admin_van_ghi_du_lieu_binh_thuong(client):
    admin_headers = auth_headers(client, "admin", "secret123")

    tao_danh_muc_response = client.post(
        "/api/v1/categories",
        json={"ten_danh_muc": "Ống kính", "mo_ta": "Danh mục test"},
        headers=admin_headers,
    )
    assert tao_danh_muc_response.status_code == 201, tao_danh_muc_response.text
    category_id = tao_danh_muc_response.json()["id_danh_muc"]

    tao_thiet_bi_response = client.post(
        "/api/v1/devices",
        json={
            "ten_thiet_bi": "Sony FX3",
            "id_danh_muc": category_id,
            "gia_thue": 1200000,
            "so_luong": 2,
            "tinh_trang": "San sang",
        },
        headers=admin_headers,
    )
    assert tao_thiet_bi_response.status_code == 201, tao_thiet_bi_response.text

    tao_ma_response = client.post(
        "/api/v1/admin/discounts",
        json={
            "ma_code": "ADMINOK",
            "ten_ma": "Admin OK",
            "loai_giam_gia": "phan_tram",
            "gia_tri_giam": 20,
            "dieu_kien_loai": "khong_dieu_kien",
            "so_luong": 2,
            "trang_thai": "dang_hoat_dong",
        },
        headers=admin_headers,
    )
    assert tao_ma_response.status_code == 201, tao_ma_response.text
    discount_id = tao_ma_response.json()["id_ma_giam_gia"]

    cap_nhat_ma_response = client.patch(
        f"/api/v1/admin/discounts/{discount_id}/status",
        json={"trang_thai": "tam_ngung"},
        headers=admin_headers,
    )
    assert cap_nhat_ma_response.status_code == 200, cap_nhat_ma_response.text
    assert cap_nhat_ma_response.json()["trang_thai"] == "tam_ngung"
