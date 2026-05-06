from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str, str]:
    register_payload = {
        "site_name": "Relations Site",
        "full_name": "Admin User",
        "email": email,
        "password": "StrongPass123",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    site_id = register_resp.json()["site_id"]
    user_id = register_resp.json()["id"]

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": register_payload["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return token, site_id, user_id


def test_resident_relation_crud_and_overlap_guard(client: TestClient) -> None:
    token, site_id, user_id = _register_and_login(client, "relation-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "C Blok", "code": "C"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "11", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert flat_resp.status_code == 201
    flat_id = flat_resp.json()["id"]

    relation_resp = client.post(
        "/api/v1/resident-relations",
        json={
            "user_id": user_id,
            "flat_id": flat_id,
            "relation_type": "owner",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "is_primary": True,
        },
        headers=headers,
    )
    assert relation_resp.status_code == 201
    relation_id = relation_resp.json()["id"]

    overlap_resp = client.post(
        "/api/v1/resident-relations",
        json={
            "user_id": user_id,
            "flat_id": flat_id,
            "relation_type": "tenant",
            "start_date": "2026-06-01",
            "end_date": "2027-01-01",
            "is_primary": False,
        },
        headers=headers,
    )
    assert overlap_resp.status_code == 409

    list_resp = client.get("/api/v1/resident-relations", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.patch(
        f"/api/v1/resident-relations/{relation_id}",
        json={"end_date": "2026-11-30"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["end_date"] == "2026-11-30"

    delete_resp = client.delete(f"/api/v1/resident-relations/{relation_id}", headers=headers)
    assert delete_resp.status_code == 204


def test_resident_relation_tenant_guard(client: TestClient) -> None:
    token, site_id, user_id = _register_and_login(client, "relation-tenant@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "D Blok", "code": "D"},
        headers=headers,
    )
    assert block_resp.status_code == 201

    flat_resp = client.post(
        "/api/v1/flats",
        json={
            "block_id": block_resp.json()["id"],
            "unit_no": "21",
            "floor": 2,
            "status": "active",
        },
        headers=headers,
    )
    assert flat_resp.status_code == 201

    mismatch_headers = {"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"}
    mismatch_resp = client.post(
        "/api/v1/resident-relations",
        json={
            "user_id": user_id,
            "flat_id": flat_resp.json()["id"],
            "relation_type": "owner",
            "start_date": "2026-01-01",
            "end_date": None,
            "is_primary": False,
        },
        headers=mismatch_headers,
    )
    assert mismatch_resp.status_code == 403
