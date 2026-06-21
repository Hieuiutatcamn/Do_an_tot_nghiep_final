def test_list_search_filter_devices(client):
    response = client.get("/api/v1/devices", params={"search": "Sony", "available_only": True})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["ten_thiet_bi"] == "Sony A7III"


def test_device_availability(client):
    response = client.get("/api/v1/devices/1/availability")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["con_hang"] is True
    assert data["so_luong"] == 2
