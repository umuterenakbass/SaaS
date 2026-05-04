from fastapi.testclient import TestClient


def test_register_login_and_access_protected_endpoints(client: TestClient) -> None:
    register_payload = {
        "site_name": "Green Park Site",
        "full_name": "Admin User",
        "email": "admin@greenpark.com",
        "password": "StrongPass123",
    }

    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    registered_user = register_resp.json()
    assert registered_user["role"] == "admin"

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Site-Id": registered_user["site_id"],
    }

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == register_payload["email"]

    tenant_resp = client.get("/api/v1/tenant/context", headers=headers)
    assert tenant_resp.status_code == 200
    assert tenant_resp.json()["site_id"] == registered_user["site_id"]

    admin_area_resp = client.get("/api/v1/tenant/admin-area", headers=headers)
    assert admin_area_resp.status_code == 200


def test_tenant_mismatch_returns_403(client: TestClient) -> None:
    register_payload = {
        "site_name": "Blue Park Site",
        "full_name": "Admin User",
        "email": "admin@bluepark.com",
        "password": "StrongPass123",
    }

    client.post("/api/v1/auth/register", json=register_payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": register_payload["email"], "password": register_payload["password"]},
    )
    token = login_resp.json()["access_token"]

    mismatch_headers = {
        "Authorization": f"Bearer {token}",
        "X-Site-Id": "wrong-site-id",
    }

    tenant_resp = client.get("/api/v1/tenant/context", headers=mismatch_headers)
    assert tenant_resp.status_code == 403
    assert tenant_resp.json()["detail"] == "Tenant context mismatch"
