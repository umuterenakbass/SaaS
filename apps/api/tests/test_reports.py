from fastapi.testclient import TestClient


def _setup(client: TestClient, email: str) -> tuple[str, str, str]:
    """Register + login + block + flat, return (token, site_id, flat_id)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"site_name": f"Report Site {email}", "full_name": "Admin", "email": email, "password": "StrongPass123"},
    )
    assert reg.status_code == 201
    site_id = reg.json()["site_id"]

    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_id = client.post("/api/v1/blocks", json={"name": "R Blok", "code": "R"}, headers=headers).json()["id"]
    flat_id = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    ).json()["id"]
    return token, site_id, flat_id


def _create_charge(client: TestClient, headers: dict, flat_id: str, period: str, amount: str = "1500.00") -> str:
    resp = client.post(
        "/api/v1/charges",
        json={"flat_id": flat_id, "charge_type": "aidat", "period": period,
              "amount": amount, "due_date": f"{period}-15", "status": "pending"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_payment(client: TestClient, headers: dict, flat_id: str, period: str, amount: str = "1500.00") -> str:
    resp = client.post(
        "/api/v1/payments",
        json={"flat_id": flat_id, "amount": amount, "paid_at": f"{period}-10T10:00:00Z",
              "method": "bank_transfer", "reference_no": None, "note": None},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_period_summary_basic(client: TestClient) -> None:
    token, site_id, flat_id = _setup(client, "report-period@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    _create_charge(client, headers, flat_id, "2026-07", "2000.00")
    _create_payment(client, headers, flat_id, "2026-07", "2000.00")

    resp = client.get("/api/v1/reports/period-summary?period=2026-07", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "2026-07"
    assert float(data["total_charges"]) == 2000.0
    assert float(data["total_payments"]) == 2000.0
    assert data["charge_count"] == 1
    assert data["payment_count"] == 1
    assert len(data["by_charge_type"]) == 1
    assert data["by_charge_type"][0]["charge_type"] == "aidat"


def test_period_summary_collection_rate(client: TestClient) -> None:
    token, site_id, flat_id = _setup(client, "report-rate@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    charge_id = _create_charge(client, headers, flat_id, "2026-08", "1000.00")
    payment_id = _create_payment(client, headers, flat_id, "2026-08", "500.00")

    # Ödemeyi borca tahsis et → collection_rate = 50%
    client.post(
        "/api/v1/payment-allocations",
        json={"payment_id": payment_id, "charge_id": charge_id, "allocated_amount": "500.00"},
        headers=headers,
    )

    resp = client.get("/api/v1/reports/period-summary?period=2026-08", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["total_allocated"]) == 500.0
    assert float(data["collection_rate"]) == 50.0


def test_flat_summary_basic(client: TestClient) -> None:
    token, site_id, flat_id = _setup(client, "report-flat@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    _create_charge(client, headers, flat_id, "2026-09", "3000.00")
    _create_payment(client, headers, flat_id, "2026-09", "1500.00")

    resp = client.get("/api/v1/reports/flat-summary?period=2026-09", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["flat_count"] == 1
    item = data["items"][0]
    assert item["flat_id"] == flat_id
    assert float(item["total_charges"]) == 3000.0
    assert float(item["total_payments"]) == 1500.0
    assert float(item["balance"]) == 1500.0


def test_flat_summary_all_periods(client: TestClient) -> None:
    token, site_id, flat_id = _setup(client, "report-allperiods@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    _create_charge(client, headers, flat_id, "2026-09", "1000.00")
    _create_charge(client, headers, flat_id, "2026-10", "1000.00")

    resp = client.get("/api/v1/reports/flat-summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] is None
    assert float(data["items"][0]["total_charges"]) == 2000.0


def test_export_charges_csv(client: TestClient) -> None:
    token, site_id, flat_id = _setup(client, "report-csv-charges@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    _create_charge(client, headers, flat_id, "2026-10")

    resp = client.get("/api/v1/reports/export/charges?period=2026-10", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("id,flat_id")
    assert len(lines) == 2  # header + 1 row


def test_export_payments_csv(client: TestClient) -> None:
    token, site_id, flat_id = _setup(client, "report-csv-payments@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    _create_payment(client, headers, flat_id, "2026-10")

    resp = client.get("/api/v1/reports/export/payments?period=2026-10", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    lines = resp.text.strip().splitlines()
    assert lines[0].startswith("id,flat_id")
    assert len(lines) == 2


def test_tenant_isolation_reports(client: TestClient) -> None:
    token_a, site_a, flat_a = _setup(client, "report-iso-a@example.com")
    token_b, site_b, _ = _setup(client, "report-iso-b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Site-Id": site_a}
    _create_charge(client, headers_a, flat_a, "2026-11")

    headers_b = {"Authorization": f"Bearer {token_b}", "X-Site-Id": site_b}
    resp = client.get("/api/v1/reports/period-summary?period=2026-11", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json()["charge_count"] == 0
