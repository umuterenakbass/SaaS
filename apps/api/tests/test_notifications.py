from fastapi.testclient import TestClient


def _setup(client: TestClient, email: str) -> tuple[str, str, str, str, str]:
    """Register, login, create block + flat, return (token, site_id, flat_id, charge_id, payment_id)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "site_name": "Notif Site",
            "full_name": "Admin",
            "email": email,
            "password": "StrongPass123",
        },
    )
    assert reg.status_code == 201
    site_id = reg.json()["site_id"]

    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_id = client.post("/api/v1/blocks", json={"name": "N Blok", "code": "N"}, headers=headers).json()["id"]
    flat_id = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    ).json()["id"]

    charge_resp = client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "aidat",
            "period": "2026-06",
            "amount": "2000.00",
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
            "amount": "2000.00",
            "paid_at": "2026-06-10T10:00:00Z",
            "method": "bank_transfer",
            "reference_no": None,
            "note": None,
        },
        headers=headers,
    )
    assert payment_resp.status_code == 201
    payment_id = payment_resp.json()["id"]

    return token, site_id, flat_id, charge_id, payment_id


def test_notifications_created_on_charge_and_payment(client: TestClient) -> None:
    token, site_id, flat_id, charge_id, payment_id = _setup(
        client, "notif-test@example.com"
    )
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    resp = client.get("/api/v1/notifications", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    types = {item["notification_type"] for item in items}
    assert "charge_created" in types
    assert "payment_received" in types


def test_unread_count(client: TestClient) -> None:
    token, site_id, *_ = _setup(client, "notif-count@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    resp = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["unread_count"] >= 2


def test_mark_as_read(client: TestClient) -> None:
    token, site_id, *_ = _setup(client, "notif-read@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    notifs = client.get("/api/v1/notifications", headers=headers).json()
    first_id = notifs[0]["id"]

    patch_resp = client.patch(f"/api/v1/notifications/{first_id}/read", headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_read"] is True


def test_mark_all_as_read(client: TestClient) -> None:
    token, site_id, *_ = _setup(client, "notif-readall@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    resp = client.patch("/api/v1/notifications/read-all", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 0

    count_resp = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_resp.json()["unread_count"] == 0


def test_filter_unread(client: TestClient) -> None:
    token, site_id, *_ = _setup(client, "notif-filter@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    unread = client.get("/api/v1/notifications?is_read=false", headers=headers).json()
    assert all(item["is_read"] is False for item in unread)


def test_trigger_overdue(client: TestClient) -> None:
    token, site_id, flat_id, *_ = _setup(client, "notif-overdue@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    # Vadesi geçmiş borç oluştur
    client.post(
        "/api/v1/charges",
        json={
            "flat_id": flat_id,
            "charge_type": "su",
            "period": "2025-01",
            "amount": "500.00",
            "due_date": "2025-01-31",
            "status": "pending",
        },
        headers=headers,
    )

    resp = client.post("/api/v1/notifications/trigger-overdue", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["unread_count"] >= 1

    # İdempotent — tekrar çalıştırınca yeni bildirim oluşmamalı
    resp2 = client.post("/api/v1/notifications/trigger-overdue", headers=headers)
    assert resp2.json()["unread_count"] == 0


def test_tenant_isolation(client: TestClient) -> None:
    token_a, site_a, *_ = _setup(client, "notif-tenant-a@example.com")
    token_b, site_b, *_ = _setup(client, "notif-tenant-b@example.com")

    headers_b = {"Authorization": f"Bearer {token_b}", "X-Site-Id": site_b}
    notifs_b = client.get("/api/v1/notifications", headers=headers_b).json()
    notif_ids_b = {n["id"] for n in notifs_b}

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Site-Id": site_a}
    notifs_a = client.get("/api/v1/notifications", headers=headers_a).json()
    notif_ids_a = {n["id"] for n in notifs_a}

    assert notif_ids_a.isdisjoint(notif_ids_b)
