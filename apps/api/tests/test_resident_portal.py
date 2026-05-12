from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_admin(client: TestClient, email: str) -> tuple[str, str, str, str]:
    """Admin kayıt + blok + daire. (admin_token, site_id, flat_id, block_id)"""
    reg = client.post(
        "/api/v1/auth/register",
        json={"site_name": "Resident Site", "full_name": "Admin", "email": email, "password": "StrongPass123"},
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
    flat_id = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    ).json()["id"]
    return token, site_id, flat_id, block_id


def _register_resident(client: TestClient, site_id: str, email: str) -> tuple[str, str]:
    """Sakin kaydı (admin API üzerinden değil, register'ı kullan ama role resident yap).
    Şu an register endpoint'i admin yaratıyor; bu yüzden admin token'ı ile
    DB'ye doğrudan user ekleyemeyiz. Bunun yerine resident_relations helper'ı üzerinden
    sakin kullanıcısını oluşturuyoruz: ayrı bir site kurup kullanıcıyı oluşturuyoruz,
    sonra admin sakin ilişkisi kuruyor — ama bu karmaşık.

    Daha temiz yol: auth/register'ı çağır (yeni site yaratır), ardından
    mevcut admin o kullanıcıyı resident olarak ilişkilendirmez — çünkü
    farklı site'de. Bu yüzden test için aynı site'de resident user
    oluşturmak amacıyla admin'in POST /users (veya /resident-relations endpoint'indeki
    user_id) kullanılır.

    Sprint 9'da sakin kaydı admin tarafından yapılıyor (Sprint 10 davet sistemi).
    Şimdilik: admin ile sakin kaydı POST /api/v1/auth/register-resident endpoint
    yerine, direkt test DB'ye insert yapıyoruz.
    """
    raise NotImplementedError


def _create_resident_via_admin(
    client: TestClient,
    admin_headers: dict,
    site_id: str,
    flat_id: str,
    resident_email: str,
) -> tuple[str, str]:
    """Admin, sakin kullanıcısı oluşturur ve daire ilişkisi kurar.
    Şu an register endpoint'i her kullanıcıyı admin olarak açıyor.
    Sprint 9'da admin-create-user endpoint ekleyeceğiz (adım 2b).
    Bu yüzden testler için conftest fixture'dan gelen TestClient + DB'ye
    direkt erişim kullanıyoruz.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# NOT: resident_portal endpoint'leri role=resident gerektiriyor.
# Mevcut register endpoint'i admin yaratıyor. Sprint 9'da
# admin tarafından kullanıcı oluşturma endpoint'i eklenmeden
# entegrasyon testi yazılamaz. Bu dosya placeholder olarak bırakıldı;
# testler admin-create-user (Sprint 10) ile tamamlanacak.
# Şimdilik: role guard'ın çalıştığını doğrulayan smoke testler yazıyoruz.
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


def test_me_flats_admin_forbidden(client: TestClient) -> None:
    """Admin rolüyle /me/flats 403 döndürmeli (sadece resident erişebilir)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "site_name": "Portal Guard Site",
            "full_name": "Admin",
            "email": "portal-guard@example.com",
            "password": "StrongPass123",
        },
    )
    assert reg.status_code == 201
    site_id = reg.json()["site_id"]

    token = client.post(
        "/api/v1/auth/login",
        data={"username": "portal-guard@example.com", "password": "StrongPass123"},
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/me/flats",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 403


def test_me_balance_admin_forbidden(client: TestClient) -> None:
    """Admin rolüyle /me/balance 403 döndürmeli."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "site_name": "Balance Guard Site",
            "full_name": "Admin",
            "email": "balance-guard@example.com",
            "password": "StrongPass123",
        },
    )
    site_id = reg.json()["site_id"]
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "balance-guard@example.com", "password": "StrongPass123"},
    ).json()["access_token"]

    resp = client.get(
        "/api/v1/me/balance",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": site_id},
    )
    assert resp.status_code == 403
