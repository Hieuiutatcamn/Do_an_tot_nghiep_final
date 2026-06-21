from tests.conftest import auth_headers


def test_admin_can_crud_accounts_customers_and_employees(client):
    admin_headers = auth_headers(client, "admin", "secret123")

    account_response = client.post(
        "/api/v1/accounts",
        json={
            "dang_nhap": "nv04",
            "mat_khau": "123456",
            "vai_tro": "Nhan vien",
            "trang_thai": "Hoat dong",
            "key": True,
        },
        headers=admin_headers,
    )
    assert account_response.status_code == 201, account_response.text
    account_id = account_response.json()["id_tai_khoan"]

    list_accounts_response = client.get("/api/v1/accounts", headers=admin_headers)
    assert list_accounts_response.status_code == 200, list_accounts_response.text
    assert list_accounts_response.json()["total"] >= 3

    password_response = client.patch(
        f"/api/v1/accounts/{account_id}/password",
        json={"mat_khau": "new123456"},
        headers=admin_headers,
    )
    assert password_response.status_code == 200, password_response.text

    employee_response = client.post(
        "/api/v1/employees",
        json={
            "id_tai_khoan": account_id,
            "ho_ten": "Le Van Nam",
            "sdt": "0901000003",
        },
        headers=admin_headers,
    )
    assert employee_response.status_code == 201, employee_response.text
    employee_id = employee_response.json()["id_nhan_vien"]

    duplicate_employee_response = client.post(
        "/api/v1/employees",
        json={"id_tai_khoan": account_id, "ho_ten": "Duplicate"},
        headers=admin_headers,
    )
    assert duplicate_employee_response.status_code == 409

    update_employee_response = client.put(
        f"/api/v1/employees/{employee_id}",
        json={"ho_ten": "Le Van Nam Updated"},
        headers=admin_headers,
    )
    assert update_employee_response.status_code == 200, update_employee_response.text
    assert update_employee_response.json()["ho_ten"] == "Le Van Nam Updated"

    customer_account_response = client.post(
        "/api/v1/accounts",
        json={
            "dang_nhap": "kh99",
            "mat_khau": "123456",
            "vai_tro": "Khach hang",
            "trang_thai": "Hoat dong",
            "key": True,
        },
        headers=admin_headers,
    )
    assert customer_account_response.status_code == 201, customer_account_response.text
    customer_account_id = customer_account_response.json()["id_tai_khoan"]

    customer_response = client.post(
        "/api/v1/customers",
        json={
            "id_tai_khoan": customer_account_id,
            "ho_ten": "Tran Thi Test",
            "sdt": "0919999999",
            "email": "customer99@example.com",
        },
        headers=admin_headers,
    )
    assert customer_response.status_code == 201, customer_response.text
    customer_id = customer_response.json()["id_khach_hang"]

    update_customer_response = client.put(
        f"/api/v1/customers/{customer_id}",
        json={"ho_ten": "Tran Thi Test Updated"},
        headers=admin_headers,
    )
    assert update_customer_response.status_code == 200, update_customer_response.text
    assert update_customer_response.json()["ho_ten"] == "Tran Thi Test Updated"

    deactivate_response = client.delete(f"/api/v1/accounts/{account_id}", headers=admin_headers)
    assert deactivate_response.status_code == 200, deactivate_response.text
    assert deactivate_response.json()["trang_thai"] == "Ngung hoat dong"
    assert deactivate_response.json()["key"] is False


def test_admin_only_resources_reject_customer(client):
    customer_headers = auth_headers(client)
    response = client.get("/api/v1/employees", headers=customer_headers)
    assert response.status_code == 403
