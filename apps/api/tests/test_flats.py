from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Flats Site",
        "full_name": "Admin User",
        "email": email,
        "password": "StrongPass123",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    site_id = register_resp.json()["site_id"]

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": register_payload["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return token, site_id


def test_flats_create_list_and_duplicate_guard(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "flats-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "B Blok", "code": "B"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    create_flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert create_flat_resp.status_code == 201
    flat_id = create_flat_resp.json()["id"]

    duplicate_flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 2, "status": "active"},
        headers=headers,
    )
    assert duplicate_flat_resp.status_code == 409

    list_resp = client.get("/api/v1/flats", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.patch(
        f"/api/v1/flats/{flat_id}",
        json={"unit_no": "2", "floor": 2},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["unit_no"] == "2"

    delete_resp = client.delete(f"/api/v1/flats/{flat_id}", headers=headers)
    assert delete_resp.status_code == 204

    recreate_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "2", "floor": 3, "status": "active"},
        headers=headers,
    )
    assert recreate_resp.status_code == 201

    list_after_recreate = client.get("/api/v1/flats", headers=headers)
    assert list_after_recreate.status_code == 200
    assert len(list_after_recreate.json()) == 1
    assert list_after_recreate.json()[0]["unit_no"] == "2"
