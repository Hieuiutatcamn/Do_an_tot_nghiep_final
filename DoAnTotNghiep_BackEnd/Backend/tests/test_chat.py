from tests.conftest import auth_headers


def test_customer_message_is_forwarded_without_automatic_reply(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/v1/chat/send",
        json={"noi_dung": "Shop còn Sony A7III không?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Nhân viên sẽ phản hồi bạn sớm nhất."
    assert data["conversation"]["chat_mode"] == "STAFF"
    assert data["conversation"]["trang_thai"] == "CHO_NHAN_VIEN"
    assert data["user_message"]["sender_type"] == "CUSTOMER"
    assert data["reply_message"] is None
    assert len(data["messages"]) == 1

    conversation_id = data["conversation"]["id_cuoc_tro_chuyen"]
    history_response = client.get(f"/api/v1/chat/messages/{conversation_id}", headers=headers)
    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    assert len(history) == 1
    assert {item["sender_type"] for item in history} == {"CUSTOMER"}

    removed_endpoint = client.post(
        "/api/v1/chat/messages",
        json={"noi_dung": "Không còn chatbot"},
        headers=headers,
    )
    assert removed_endpoint.status_code in {404, 405}


def test_customer_and_admin_share_staff_conversation_history(client):
    customer_headers = auth_headers(client)
    admin_headers = auth_headers(client, "admin", "secret123")

    request_staff = client.post(
        "/api/v1/chat/request-staff",
        json={},
        headers=customer_headers,
    )
    assert request_staff.status_code == 200, request_staff.text
    request_data = request_staff.json()
    conversation_id = request_data["conversation"]["id_cuoc_tro_chuyen"]
    assert request_data["success"] is True
    assert request_data["staff_online"] is False
    assert request_data["message"] == "Nhân viên hiện offline, hệ thống đã ghi nhận yêu cầu của bạn."
    assert request_data["conversation"]["chat_mode"] == "STAFF"
    assert request_data["conversation"]["trang_thai"] == "CHO_NHAN_VIEN"
    assert request_data["conversation"]["need_staff"] is True
    assert request_data["messages"] == []

    duplicate_request = client.post(
        "/api/v1/chat/request-staff",
        json={"conversation_id": conversation_id},
        headers=customer_headers,
    )
    assert duplicate_request.status_code == 200, duplicate_request.text
    assert duplicate_request.json()["conversation"]["id_cuoc_tro_chuyen"] == conversation_id

    first_message = client.post(
        "/api/v1/chat/send-staff-message",
        json={"conversation_id": conversation_id, "message": "Xin chào nhân viên"},
        headers=customer_headers,
    )
    assert first_message.status_code == 200, first_message.text

    alias_message = client.post(
        "/api/v1/chat/send-staff-message",
        json={"id_cuoc_tro_chuyen": conversation_id, "noi_dung_tin_nhan": "Tôi cần hỗ trợ đơn thuê"},
        headers=customer_headers,
    )
    assert alias_message.status_code == 200, alias_message.text

    admin_conversations = client.get("/api/v1/admin/chat/conversations", headers=admin_headers)
    assert admin_conversations.status_code == 200, admin_conversations.text
    assert admin_conversations.json()["unread_message_count"] == 2
    assert admin_conversations.json()["waiting_count"] == 1

    admin_history = client.get(
        f"/api/v1/admin/chat/messages/{conversation_id}",
        headers=admin_headers,
    )
    assert admin_history.status_code == 200, admin_history.text
    assert all(
        item["da_doc"]
        for item in admin_history.json()
        if item["sender_type"] == "CUSTOMER"
    )

    after_read = client.get("/api/v1/admin/chat/conversations", headers=admin_headers)
    assert after_read.status_code == 200, after_read.text
    assert after_read.json()["unread_message_count"] == 0
    assert after_read.json()["waiting_count"] == 0

    admin_reply = client.post(
        "/api/v1/admin/chat/reply",
        json={"conversation_id": conversation_id, "message": "SunLens đã nhận yêu cầu của bạn"},
        headers=admin_headers,
    )
    assert admin_reply.status_code == 200, admin_reply.text

    customer_history = client.get(
        f"/api/v1/chat/messages/{conversation_id}",
        headers=customer_headers,
    )
    assert customer_history.status_code == 200, customer_history.text
    messages = customer_history.json()
    assert any(item["sender_type"] == "STAFF" for item in messages)
    assert {item["sender_type"] for item in messages} == {"CUSTOMER", "STAFF"}

    reloaded_history = client.get(
        f"/api/v1/chat/messages/{conversation_id}",
        headers=customer_headers,
    )
    assert reloaded_history.status_code == 200, reloaded_history.text
    assert reloaded_history.json() == messages


def test_online_employee_is_assigned_to_new_conversation(client):
    customer_headers = auth_headers(client)
    admin_headers = auth_headers(client, "admin", "secret123")

    online_response = client.put(
        "/api/v1/admin/staff/online",
        json={"is_online": True},
        headers=admin_headers,
    )
    assert online_response.status_code == 200, online_response.text

    send_response = client.post(
        "/api/v1/chat/send",
        json={"message": "Tôi cần hỗ trợ đơn thuê"},
        headers=customer_headers,
    )
    assert send_response.status_code == 200, send_response.text
    data = send_response.json()
    assert data["staff_online"] is True
    assert data["message"] == "Đã gửi yêu cầu hỗ trợ."
    assert data["conversation"]["id_nhan_vien"] == online_response.json()["id_nhan_vien"]
    assert data["conversation"]["trang_thai"] == "NHAN_VIEN_DANG_XU_LY"

    request_staff = client.post(
        "/api/v1/chat/request-staff",
        json={"conversation_id": data["conversation"]["id_cuoc_tro_chuyen"]},
        headers=customer_headers,
    )
    assert request_staff.status_code == 200, request_staff.text
    request_data = request_staff.json()
    assert request_data["success"] is True
    assert request_data["staff_online"] is True
    assert request_data["message"] == "Đã kết nối với nhân viên hỗ trợ."
    assert request_data["conversation"]["chat_mode"] == "STAFF"
    assert request_data["conversation"]["trang_thai"] == "NHAN_VIEN_DANG_XU_LY"
    assert request_data["conversation"]["need_staff"] is True
    assert request_data["messages"] == []
