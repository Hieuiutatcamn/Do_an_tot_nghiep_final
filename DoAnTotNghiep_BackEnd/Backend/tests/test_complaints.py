from tests.conftest import auth_headers


def test_customer_can_create_and_view_own_complaints(client):
    customer_headers = auth_headers(client)

    create_response = client.post(
        "/api/v1/complaints",
        json={"noi_dung": "May bi loi pin"},
        headers=customer_headers,
    )
    assert create_response.status_code == 201, create_response.text
    complaint_id = create_response.json()["id_khieu_nai"]
    assert create_response.json()["trang_thai"] == "Cho phan hoi"

    get_response = client.get(f"/api/v1/complaints/{complaint_id}", headers=customer_headers)
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["noi_dung"] == "May bi loi pin"

    list_response = client.get("/api/v1/complaints", headers=customer_headers)
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] == 1

    update_response = client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json={"trang_thai": "Da xu ly"},
        headers=customer_headers,
    )
    assert update_response.status_code == 403


def test_staff_can_update_complaint_status_and_admin_can_delete(client):
    customer_headers = auth_headers(client)
    create_response = client.post(
        "/api/v1/complaints",
        json={"noi_dung": "Thiet bi giao tre"},
        headers=customer_headers,
    )
    assert create_response.status_code == 201, create_response.text
    complaint_id = create_response.json()["id_khieu_nai"]

    admin_headers = auth_headers(client, "admin", "secret123")
    status_response = client.patch(
        f"/api/v1/complaints/{complaint_id}/status",
        json={"trang_thai": "Dang xu ly"},
        headers=admin_headers,
    )
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["trang_thai"] == "Dang xu ly"

    delete_response = client.delete(f"/api/v1/complaints/{complaint_id}", headers=admin_headers)
    assert delete_response.status_code == 204, delete_response.text


def test_openapi_contains_new_routers(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    paths = response.json()["paths"]
    assert "/api/v1/tai-khoan" in paths
    assert "/api/v1/khach-hang" in paths
    assert "/api/v1/nhan-vien" in paths
    assert "/api/v1/khieu-nai" in paths
    assert "/api/v1/rentals" in paths
    assert "/api/v1/don-thue" not in paths
    assert "/api/v1/accounts" not in paths

    legacy_response = client.get("/api/v1/accounts", headers=auth_headers(client, "admin", "secret123"))
    assert legacy_response.status_code == 200, legacy_response.text
