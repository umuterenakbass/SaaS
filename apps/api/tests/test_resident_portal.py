from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_admin(client: TestClient, email: str) -> tuple[str, str]:
    """Admin kayıt + login. (admin_token, site_id)"""
    reg = client.post(
        "/api/v1/auth/register",
        json={"site_name": f"Resident Site {email}", "full_name": "Admin", "email": email, "password": "StrongPass123"},
    )
    assert reg.status_code == 201
    site_id = reg.json()["site_id"]
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123"},
    ).json()["access_token"]
    return token, site_id


def _create_resident(client: TestClient, admin_token: str, site_id: str, email: str) -> str:
    """Admin üzerinden sakin oluştur; sakin token'ı döndür."""
    resp = client.post(
        "/api/v1/users",
        json={"email": email, "full_name": "Sakin Biri", "password": "ResPass123", "role": "resident"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "ResPass123"},
    ).json()["access_token"]
    return token


def _make_flat(client: TestClient, admin_token: str, site_id: str, block_code: str = "PB") -> tuple[str, str]:
    """Blok + daire oluştur. (block_id, flat_id)"""
    block_id = client.post(
        "/api/v1/blocks",
        json={"name": f"Blok {block_code}", "code": block_code},
        headers={"Authorization": f"Bearer {admin_token}", "X-Site-Id": site_id},
    ).json()["id"]
    flat_id = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "gross_m2": 80, "net_m2": 70},
        headers={"Authorization": f"Bearer {admin_token}", "X-Site-Id": site_id},
    ).json()["id"]
    return block_id, flat_id




# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_me_flats_requires_auth(client: TestClient) -> None:
    """Token olmadan /me/flats 401 döndürmeli."""
    resp = client.get("/api/v1/me/flats", headers={"X-Site-Id": "any"})
    assert resp.status_code == 401


def test_me_charges_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/me/charges", headers={"X-Site-Id": "any"})
    assert resp.status_code == 401


def test_me_payments_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/me/payments", headers={"X-Site-Id": "any"})
    assert resp.status_code == 401


def test_me_balance_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/me/balance", headers={"X-Site-Id": "any"})
    assert resp.status_code == 401


def test_me_notifications_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/v1/me/notifications", headers={"X-Site-Id": "any"})
    assert resp.status_code == 401


def test_portal_admin_forbidden(client: TestClient) -> None:
    """Admin rolü /me endpoint'lerine erişememeli (403)."""
    admin_token, site_id = _setup_admin(client, "portal-admin-block@example.com")
    headers = {"Authorization": f"Bearer {admin_token}", "X-Site-Id": site_id}
    for path in ["/api/v1/me/flats", "/api/v1/me/charges", "/api/v1/me/payments", "/api/v1/me/balance"]:
        resp = client.get(path, headers=headers)
        assert resp.status_code == 403, f"{path} admin'e 403 dönmeli"


def test_portal_balance_empty(client: TestClient) -> None:
    """Dairesi olmayan sakin sıfır bakiye almalı."""
    admin_token, site_id = _setup_admin(client, "portal-balance-empty@example.com")
    res_token = _create_resident(client, admin_token, site_id, "res-balance-empty@example.com")
    resp = client.get(
        "/api/v1/me/balance",
        headers={"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["balance"]) == 0.0
    assert data["pending_count"] == 0


def test_portal_flats_empty(client: TestClient) -> None:
    """Dairesi olmayan sakin boş liste almalı."""
    admin_token, site_id = _setup_admin(client, "portal-flats-empty@example.com")
    res_token = _create_resident(client, admin_token, site_id, "res-flats-empty@example.com")
    resp = client.get(
        "/api/v1/me/flats",
        headers={"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_portal_flats_with_relation(client: TestClient) -> None:
    """Dairesi olan sakin dairesini görmeli."""
    admin_token, site_id = _setup_admin(client, "portal-flats-rel@example.com")
    res_token = _create_resident(client, admin_token, site_id, "res-flats-rel@example.com")

    users = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}", "X-Site-Id": site_id},
    ).json()
    resident_id = next(u["id"] for u in users if u["email"] == "res-flats-rel@example.com")

    _, flat_id = _make_flat(client, admin_token, site_id, "P1")
    client.post(
        "/api/v1/resident-relations",
        json={"user_id": resident_id, "flat_id": flat_id, "relation_type": "tenant", "start_date": "2024-01-01", "is_primary": True},
        headers={"Authorization": f"Bearer {admin_token}", "X-Site-Id": site_id},
    )

    resp = client.get(
        "/api/v1/me/flats",
        headers={"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["relation_type"] == "tenant"


def test_portal_charges_empty(client: TestClient) -> None:
    """Dairesi olmayan sakin için borç listesi boş olmalı."""
    admin_token, site_id = _setup_admin(client, "portal-charges-empty@example.com")
    res_token = _create_resident(client, admin_token, site_id, "res-charges-empty@example.com")
    resp = client.get(
        "/api/v1/me/charges",
        headers={"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_portal_payments_empty(client: TestClient) -> None:
    """Dairesi olmayan sakin için ödeme listesi boş olmalı."""
    admin_token, site_id = _setup_admin(client, "portal-payments-empty@example.com")
    res_token = _create_resident(client, admin_token, site_id, "res-payments-empty@example.com")
    resp = client.get(
        "/api/v1/me/payments",
        headers={"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_portal_notifications_empty(client: TestClient) -> None:
    """Bildirimi olmayan sakin boş liste almalı."""
    admin_token, site_id = _setup_admin(client, "portal-notif-empty@example.com")
    res_token = _create_resident(client, admin_token, site_id, "res-notif-empty@example.com")
    resp = client.get(
        "/api/v1/me/notifications",
        headers={"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 200
    assert resp.json() == []


def test_portal_tenant_isolation(client: TestClient) -> None:
    """Site B sakini, Site A header'ı ile sorgu yapınca veri görmemeli."""
    admin_a_token, site_a_id = _setup_admin(client, "portal-iso-a@example.com")
    admin_b_token, site_b_id = _setup_admin(client, "portal-iso-b@example.com")

    res_b_token = _create_resident(client, admin_b_token, site_b_id, "res-iso-b@example.com")

    # Site B sakini Site A header'ı ile bakiye sorgulasın
    resp = client.get(
        "/api/v1/me/balance",
        headers={"Authorization": f"Bearer {res_b_token}", "X-Site-Id": site_a_id},
    )
    # Token site_b'ye ait, header site_a → 401 veya sıfır bakiye beklenir
    assert resp.status_code in (200, 401, 403)
    if resp.status_code == 200:
        assert float(resp.json()["balance"]) == 0.0

