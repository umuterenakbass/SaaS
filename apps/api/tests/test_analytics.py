from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client: TestClient, email: str) -> tuple[str, str, str, str]:
    """Admin kayıt + blok + 3 daire. (token, site_id, flat_id1, flat_id2)"""
    reg = client.post(
        "/api/v1/auth/register",
        json={"site_name": f"Analytics Site {email}", "full_name": "Admin", "email": email, "password": "StrongPass123"},
    )
    assert reg.status_code == 201
    site_id = reg.json()["site_id"]

    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_id = client.post(
        "/api/v1/blocks", json={"name": "A Blok", "code": "A"}, headers=headers
    ).json()["id"]

    flat1 = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    ).json()["id"]
    flat2 = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "2", "floor": 1, "status": "active"},
        headers=headers,
    ).json()["id"]

    return token, site_id, flat1, flat2


def _make_headers(token: str, site_id: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_analytics_dashboard_empty(client: TestClient) -> None:
    """Verisi olmayan site için dashboard 200 döndürmeli, trend listesi boş olmamalı."""
    token, site_id, _, _ = _setup(client, "analytics-empty@example.com")
    resp = client.get(
        "/api/v1/analytics/dashboard",
        headers=_make_headers(token, site_id),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "monthly_trend" in data
    assert "occupancy" in data
    assert "charge_type_breakdown" in data
    assert len(data["monthly_trend"]) == 12  # son 12 ay


def test_analytics_monthly_trend_has_data(client: TestClient) -> None:
    """Borç ve ödeme ekleyince trend verisinde görünmeli."""
    token, site_id, flat1, _ = _setup(client, "analytics-trend@example.com")
    headers = _make_headers(token, site_id)

    client.post(
        "/api/v1/charges",
        json={"flat_id": flat1, "charge_type": "aidat", "period": "2026-04",
              "amount": "1500.00", "due_date": "2026-04-15"},
        headers=headers,
    )
    client.post(
        "/api/v1/payments",
        json={"flat_id": flat1, "amount": "1500.00", "paid_at": "2026-04-10T10:00:00Z",
              "method": "bank_transfer"},
        headers=headers,
    )

    resp = client.get("/api/v1/analytics/monthly-trend?months=12", headers=headers)
    assert resp.status_code == 200
    trend = resp.json()
    april = next((t for t in trend if t["period"] == "2026-04"), None)
    assert april is not None
    assert float(april["total_charges"]) == 1500.0
    assert april["collection_rate"] == "100.00"


def test_analytics_charge_type_breakdown(client: TestClient) -> None:
    """Farklı tipteki borçlar breakdown'da ayrı satır olmalı."""
    token, site_id, flat1, flat2 = _setup(client, "analytics-breakdown@example.com")
    headers = _make_headers(token, site_id)

    client.post("/api/v1/charges",
        json={"flat_id": flat1, "charge_type": "aidat", "period": "2026-05",
              "amount": "1500.00", "due_date": "2026-05-15"}, headers=headers)
    client.post("/api/v1/charges",
        json={"flat_id": flat2, "charge_type": "elektrik", "period": "2026-05",
              "amount": "300.00", "due_date": "2026-05-15"}, headers=headers)

    resp = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    breakdown = resp.json()["charge_type_breakdown"]
    types = [b["charge_type"] for b in breakdown]
    assert "aidat" in types
    assert "elektrik" in types


def test_analytics_flat_occupancy(client: TestClient) -> None:
    """Daire doluluk istatistikleri doğru olmalı."""
    token, site_id, flat1, flat2 = _setup(client, "analytics-occupancy@example.com")
    headers = _make_headers(token, site_id)

    resp = client.get("/api/v1/analytics/flat-occupancy", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_flats"] == 2
    assert data["active_flats"] == 2
    assert data["occupied_flats"] == 0   # henüz sakin ilişkisi yok
    assert data["vacant_flats"] == 2


def test_analytics_tenant_isolation(client: TestClient) -> None:
    """Bir sitenin verisi diğer sitenin analytics'inde görünmemeli."""
    token1, site_id1, flat1, _ = _setup(client, "analytics-iso1@example.com")
    token2, site_id2, _, _ = _setup(client, "analytics-iso2@example.com")

    headers1 = _make_headers(token1, site_id1)
    client.post("/api/v1/charges",
        json={"flat_id": flat1, "charge_type": "aidat", "period": "2026-05",
              "amount": "2000.00", "due_date": "2026-05-15"}, headers=headers1)

    # Site 2'nin dashboard'unda site 1'in borcu görünmemeli
    resp2 = client.get("/api/v1/analytics/dashboard", headers=_make_headers(token2, site_id2))
    assert resp2.status_code == 200
    breakdown2 = resp2.json()["charge_type_breakdown"]
    assert all(float(b["total_amount"]) != 2000.0 for b in breakdown2)


def test_analytics_avg_collection_rate(client: TestClient) -> None:
    """Ortalama tahsilat oranı doğru hesaplanmalı."""
    token, site_id, flat1, _ = _setup(client, "analytics-rate@example.com")
    headers = _make_headers(token, site_id)

    # 2000 borç, 1000 ödeme → %50
    client.post("/api/v1/charges",
        json={"flat_id": flat1, "charge_type": "aidat", "period": "2026-05",
              "amount": "2000.00", "due_date": "2026-05-15"}, headers=headers)
    client.post("/api/v1/payments",
        json={"flat_id": flat1, "amount": "1000.00", "paid_at": "2026-05-10T10:00:00Z",
              "method": "cash"}, headers=headers)

    resp = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    avg = float(resp.json()["avg_collection_rate"])
    assert avg == 50.0
