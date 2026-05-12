import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client: TestClient, email: str) -> tuple[str, str]:
    """Register admin + login. Returns (token, site_id)."""
    site_name = f"Site-{email}"
    reg = client.post(
        "/api/v1/auth/register",
        json={"site_name": site_name, "full_name": "Admin", "email": email, "password": "AdminPass123"},
    )
    assert reg.status_code == 201
    site_id = reg.json()["site_id"]

    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "AdminPass123"},
    ).json()["access_token"]

    return token, site_id


def _admin_headers(token: str, site_id: str) -> dict:
    return {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_users_includes_admin(client: TestClient) -> None:
    """Admin kendini listede görmeli."""
    token, site_id = _setup(client, "list-users@example.com")
    resp = client.get("/api/v1/users", headers=_admin_headers(token, site_id))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "list-users@example.com" in emails


def test_create_resident_user(client: TestClient) -> None:
    """Admin yeni sakin oluşturabilmeli."""
    token, site_id = _setup(client, "create-resident@example.com")
    resp = client.post(
        "/api/v1/users",
        json={"email": "resident1@example.com", "full_name": "Sakin Bir", "password": "Pass123", "role": "resident"},
        headers=_admin_headers(token, site_id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "resident"
    assert data["email"] == "resident1@example.com"
    assert data["site_id"] == site_id


def test_create_accountant_user(client: TestClient) -> None:
    """Admin muhasebeci oluşturabilmeli."""
    token, site_id = _setup(client, "create-accountant@example.com")
    resp = client.post(
        "/api/v1/users",
        json={"email": "accountant1@example.com", "full_name": "Muhasebeci", "password": "Pass123", "role": "accountant"},
        headers=_admin_headers(token, site_id),
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "accountant"


def test_cannot_create_admin_via_user_mgmt(client: TestClient) -> None:
    """Admin rolü bu endpoint ile oluşturulamaz."""
    token, site_id = _setup(client, "no-admin-create@example.com")
    resp = client.post(
        "/api/v1/users",
        json={"email": "admin2@example.com", "full_name": "Admin2", "password": "Pass123", "role": "admin"},
        headers=_admin_headers(token, site_id),
    )
    assert resp.status_code == 422


def test_duplicate_email_rejected(client: TestClient) -> None:
    """Aynı email iki kez eklenememeli."""
    token, site_id = _setup(client, "dup-email@example.com")
    headers = _admin_headers(token, site_id)
    payload = {"email": "dup@example.com", "full_name": "Dup", "password": "Pass123", "role": "resident"}
    assert client.post("/api/v1/users", json=payload, headers=headers).status_code == 201
    assert client.post("/api/v1/users", json=payload, headers=headers).status_code == 409


def test_update_user(client: TestClient) -> None:
    """Admin kullanıcı bilgilerini güncelleyebilmeli."""
    token, site_id = _setup(client, "update-user@example.com")
    headers = _admin_headers(token, site_id)
    user_id = client.post(
        "/api/v1/users",
        json={"email": "toupdate@example.com", "full_name": "Eski Ad", "password": "Pass123", "role": "resident"},
        headers=headers,
    ).json()["id"]

    resp = client.patch(f"/api/v1/users/{user_id}", json={"full_name": "Yeni Ad", "is_active": False}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Yeni Ad"
    assert resp.json()["is_active"] is False


def test_delete_user(client: TestClient) -> None:
    """Admin kullanıcı silebilmeli, sonra listede görünmemeli."""
    token, site_id = _setup(client, "delete-user@example.com")
    headers = _admin_headers(token, site_id)
    user_id = client.post(
        "/api/v1/users",
        json={"email": "todelete@example.com", "full_name": "Silinecek", "password": "Pass123", "role": "resident"},
        headers=headers,
    ).json()["id"]

    assert client.delete(f"/api/v1/users/{user_id}", headers=headers).status_code == 204
    ids = [u["id"] for u in client.get("/api/v1/users", headers=headers).json()]
    assert user_id not in ids


def test_tenant_isolation(client: TestClient) -> None:
    """Farklı site admin'i diğer sitenin kullanıcılarını görememeli."""
    token_a, site_a = _setup(client, "tenant-iso-a@example.com")
    token_b, site_b = _setup(client, "tenant-iso-b@example.com")

    # site_a'ya kullanıcı ekle
    client.post(
        "/api/v1/users",
        json={"email": "only-a@example.com", "full_name": "Only A", "password": "Pass123", "role": "resident"},
        headers=_admin_headers(token_a, site_a),
    )

    # site_b sadece kendi admin'ini görmeli
    resp = client.get("/api/v1/users", headers=_admin_headers(token_b, site_b))
    emails = [u["email"] for u in resp.json()]
    assert "only-a@example.com" not in emails


def test_resident_cannot_list_users(client: TestClient) -> None:
    """Sakin /users listesine erişememeli."""
    token, site_id = _setup(client, "resident-guard@example.com")
    headers = _admin_headers(token, site_id)

    # Sakin oluştur ve onun token'ını al
    client.post(
        "/api/v1/users",
        json={"email": "just-resident@example.com", "full_name": "Res", "password": "Pass123", "role": "resident"},
        headers=headers,
    )
    res_token = client.post(
        "/api/v1/auth/login",
        data={"username": "just-resident@example.com", "password": "Pass123"},
    ).json()["access_token"]
    res_headers = {"Authorization": f"Bearer {res_token}", "X-Site-Id": site_id}

    resp = client.get("/api/v1/users", headers=res_headers)
    assert resp.status_code == 403
