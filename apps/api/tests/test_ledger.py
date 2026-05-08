from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Ledger Site",
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


def test_flat_ledger_summary_and_tenant_guard(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "ledger-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "E Blok", "code": "E"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "30", "floor": 3, "status": "active"},
        headers=headers,
    )
    assert flat_resp.status_code == 201
    flat_id = flat_resp.json()["id"]

    first_charge_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "aidat",
            "period": "2026-06",
            "amount": "1500.00",
            "due_date": "2026-06-15",
            "status": "pending",
        },
        headers=headers,
    )
    assert first_charge_resp.status_code == 201
    first_charge_id = first_charge_resp.json()["id"]

    cancelled_charge_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "demirbas",
            "period": "2026-06",
            "amount": "250.00",
            "due_date": "2026-06-20",
            "status": "cancelled",
        },
        headers=headers,
    )
    assert cancelled_charge_resp.status_code == 201

    payment_resp = client.post(
        "/api/v1/payments",
        json={
            "flat_id": flat_id,
            "amount": "400.00",
            "paid_at": "2026-06-10T12:00:00Z",
            "method": "bank_transfer",
            "reference_no": "LEDGER-1",
        },
        headers=headers,
    )
    assert payment_resp.status_code == 201
    payment_id = payment_resp.json()["id"]

    allocation_resp = client.post(
        "/api/v1/payment-allocations",
        json={
            "payment_id": payment_id,
            "charge_id": first_charge_id,
            "allocated_amount": "300.00",
        },
        headers=headers,
    )
    assert allocation_resp.status_code == 201

    ledger_resp = client.get(f"/api/v1/ledger/flats/{flat_id}", headers=headers)
    assert ledger_resp.status_code == 200
    payload = ledger_resp.json()

    assert payload["total_charges"] == "1500.00"
    assert payload["total_payments"] == "400.00"
    assert payload["allocated_total"] == "300.00"
    assert payload["open_charge_total"] == "1200.00"
    assert payload["unallocated_payment_total"] == "100.00"
    assert payload["balance"] == "1100.00"
    assert payload["charge_count"] == 1
    assert payload["payment_count"] == 1
    assert len(payload["recent_charges"]) == 1
    assert len(payload["recent_payments"]) == 1
    assert payload["recent_charges"][0]["allocated_amount"] == "300.00"
    assert payload["recent_charges"][0]["remaining_amount"] == "1200.00"
    assert payload["recent_payments"][0]["allocated_amount"] == "300.00"
    assert payload["recent_payments"][0]["remaining_amount"] == "100.00"

    wrong_tenant_resp = client.get(
        f"/api/v1/ledger/flats/{flat_id}",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"},
    )
    assert wrong_tenant_resp.status_code == 403
