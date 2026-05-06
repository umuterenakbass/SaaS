from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Blocks Site",
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


def test_blocks_crud_and_tenant_guard(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "blocks-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    create_resp = client.post(
        "/api/v1/blocks",
        json={"name": "A Blok", "code": "A"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    block_id = create_resp.json()["id"]

    duplicate_resp = client.post(
        "/api/v1/blocks",
        json={"name": "A Blok Duplicate", "code": "A"},
        headers=headers,
    )
    assert duplicate_resp.status_code == 409

    list_resp = client.get("/api/v1/blocks", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    wrong_tenant_resp = client.get(
        "/api/v1/blocks",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"},
    )
    assert wrong_tenant_resp.status_code == 403

    update_resp = client.patch(
        f"/api/v1/blocks/{block_id}",
        json={"name": "A Blok Updated"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "A Blok Updated"

    delete_resp = client.delete(f"/api/v1/blocks/{block_id}", headers=headers)
    assert delete_resp.status_code == 204
