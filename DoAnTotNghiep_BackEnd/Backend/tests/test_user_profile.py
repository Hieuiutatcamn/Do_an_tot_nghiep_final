from tests.conftest import auth_headers


def test_customer_can_update_own_profile_without_admin(client):
    headers = auth_headers(client)

    response = client.put(
        "/api/v1/users/me",
        json={
            "id_tai_khoan": 999,
            "ho_ten": "Nguyen Van A Updated",
            "sdt": "0999999999",
            "email": "updated@example.com",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["customer"]["ho_ten"] == "Nguyen Van A Updated"
    assert data["customer"]["sdt"] == "0999999999"
    assert data["customer"]["email"] == "updated@example.com"
    assert data["customer"]["id_tai_khoan"] == data["account"]["id_tai_khoan"]

    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["customer"]["ho_ten"] == "Nguyen Van A Updated"
    assert me_response.json()["customer"]["email"] == "updated@example.com"


def test_customer_can_upload_avatar_and_me_returns_new_avatar(client):
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/users/upload-anh_dai_dien",
        files={
            "file": ("avatar.png", b"avatar-image", "image/png"),
        },
        data={"user_id": "1"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["anh_dai_dien"]
    assert "cccd_anh_dai_dien_" in data["anh_dai_dien"]

    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["anh_dai_dien"] == data["anh_dai_dien"]
    assert me_response.json()["account"]["anh_dai_dien"] == data["anh_dai_dien"]


def test_customer_customer_route_only_allows_owner_or_admin(client):
    owner_headers = auth_headers(client)
    owner_profile = client.get("/api/v1/users/me", headers=owner_headers).json()
    owner_customer_id = owner_profile["customer"]["id_khach_hang"]

    own_update_response = client.put(
        f"/api/v1/customers/{owner_customer_id}",
        json={"ho_ten": "Owner Update"},
        headers=owner_headers,
    )
    assert own_update_response.status_code == 200, own_update_response.text
    assert own_update_response.json()["ho_ten"] == "Owner Update"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "kh_other",
            "password": "123456",
            "ho_ten": "Other KhachHang",
            "email": "other@example.com",
        },
    )
    assert register_response.status_code == 201, register_response.text
    other_headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}
    other_profile = client.get("/api/v1/users/me", headers=other_headers).json()
    other_customer_id = other_profile["customer"]["id_khach_hang"]

    forbidden_response = client.put(
        f"/api/v1/customers/{other_customer_id}",
        json={"ho_ten": "Not Allowed"},
        headers=owner_headers,
    )
    assert forbidden_response.status_code == 403, forbidden_response.text
