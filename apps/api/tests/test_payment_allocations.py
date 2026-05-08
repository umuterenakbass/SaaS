from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Allocation Site",
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


def test_payment_allocations_rules_and_tenant_guard(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "allocation-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "A Blok", "code": "AL"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "9", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert flat_resp.status_code == 201
    flat_id = flat_resp.json()["id"]

    charge_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "aidat",
            "period": "2026-06",
            "amount": "1000.00",
            "due_date": "2026-06-15",
            "status": "pending",
        },
        headers=headers,
    )
    assert charge_resp.status_code == 201
    charge_id = charge_resp.json()["id"]

    payment_resp = client.post(
        "/api/v1/payments",
        json={
            "flat_id": flat_id,
            "amount": "800.00",
            "paid_at": "2026-06-10T10:00:00Z",
            "method": "bank_transfer",
            "reference_no": "ALLOC-1",
        },
        headers=headers,
    )
    assert payment_resp.status_code == 201
    payment_id = payment_resp.json()["id"]

    create_alloc_resp = client.post(
        "/api/v1/payment-allocations",
        json={"payment_id": payment_id, "charge_id": charge_id, "allocated_amount": "500.00"},
        headers=headers,
    )
    assert create_alloc_resp.status_code == 201
    allocation_id = create_alloc_resp.json()["id"]

    duplicate_resp = client.post(
        "/api/v1/payment-allocations",
        json={"payment_id": payment_id, "charge_id": charge_id, "allocated_amount": "100.00"},
        headers=headers,
    )
    assert duplicate_resp.status_code == 409

    second_charge_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "yakit",
            "period": "2026-06",
            "amount": "2000.00",
            "due_date": "2026-06-20",
            "status": "pending",
        },
        headers=headers,
    )
    assert second_charge_resp.status_code == 201

    exceed_payment_resp = client.post(
        "/api/v1/payment-allocations",
        json={
            "payment_id": payment_id,
            "charge_id": second_charge_resp.json()["id"],
            "allocated_amount": "400.00",
        },
        headers=headers,
    )
    assert exceed_payment_resp.status_code == 409

    list_resp = client.get("/api/v1/payment-allocations", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    wrong_tenant_resp = client.get(
        "/api/v1/payment-allocations",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"},
    )
    assert wrong_tenant_resp.status_code == 403

    delete_resp = client.delete(f"/api/v1/payment-allocations/{allocation_id}", headers=headers)
    assert delete_resp.status_code == 204
