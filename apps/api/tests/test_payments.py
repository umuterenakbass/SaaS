from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Payments Site",
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


def test_payments_crud_filter_and_tenant_guard(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "payments-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "D Blok", "code": "D"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "20", "floor": 2, "status": "active"},
        headers=headers,
    )
    assert flat_resp.status_code == 201
    flat_id = flat_resp.json()["id"]

    invalid_amount_resp = client.post(
        "/api/v1/payments",
        json={
            "flat_id": flat_id,
            "amount": "0",
            "paid_at": "2026-05-07T10:00:00Z",
            "method": "cash",
        },
        headers=headers,
    )
    assert invalid_amount_resp.status_code == 422

    create_resp = client.post(
        "/api/v1/payments",
        json={
            "flat_id": flat_id,
            "amount": "1200.00",
            "paid_at": "2026-05-07T10:00:00Z",
            "method": "bank_transfer",
            "reference_no": "REF-123",
            "note": "Mayıs ödemesi",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    payment_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/payments", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    filter_resp = client.get(f"/api/v1/payments?flat_id={flat_id}", headers=headers)
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 1

    update_resp = client.patch(
        f"/api/v1/payments/{payment_id}",
        json={"method": "cash", "note": "Nakit ödendi"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["method"] == "cash"

    wrong_tenant_resp = client.get(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"},
    )
    assert wrong_tenant_resp.status_code == 403

    delete_resp = client.delete(f"/api/v1/payments/{payment_id}", headers=headers)
    assert delete_resp.status_code == 204
