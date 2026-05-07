from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Billing Site",
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


def test_charges_crud_filter_duplicate_and_tenant_guard(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "charges-admin@example.com")
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
        json={"block_id": block_id, "unit_no": "10", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert flat_resp.status_code == 201
    flat_id = flat_resp.json()["id"]

    create_charge_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "aidat",
            "period": "2026-05",
            "amount": "1500.00",
            "due_date": "2026-05-15",
            "status": "pending",
        },
        headers=headers,
    )
    assert create_charge_resp.status_code == 201
    charge_id = create_charge_resp.json()["id"]

    duplicate_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "aidat",
            "period": "2026-05",
            "amount": "1200.00",
            "due_date": "2026-05-20",
            "status": "pending",
        },
        headers=headers,
    )
    assert duplicate_resp.status_code == 409

    list_resp = client.get("/api/v1/charges", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    filter_resp = client.get("/api/v1/charges?period=2026-05", headers=headers)
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 1

    update_resp = client.patch(
        f"/api/v1/charges/{charge_id}",
        json={"status": "paid", "amount": "1500.00"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "paid"

    wrong_tenant_resp = client.get(
        "/api/v1/charges",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"},
    )
    assert wrong_tenant_resp.status_code == 403

    delete_resp = client.delete(f"/api/v1/charges/{charge_id}", headers=headers)
    assert delete_resp.status_code == 204
