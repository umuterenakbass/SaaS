from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client: TestClient, email: str) -> tuple[str, str, list[str]]:
    """Register + login + block + 3 flats. Returns (token, site_id, [flat_id1, flat_id2, flat_id3])."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"site_name": "Bulk Site", "full_name": "Admin", "email": email, "password": "StrongPass123"},
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

    flat_ids = []
    for i in range(1, 4):
        fid = client.post(
            "/api/v1/flats",
            json={"block_id": block_id, "unit_no": str(i), "floor": 1, "status": "active"},
            headers=headers,
        ).json()["id"]
        flat_ids.append(fid)

    return token, site_id, flat_ids


# ---------------------------------------------------------------------------
# Bulk charge tests
# ---------------------------------------------------------------------------

def test_bulk_charge_all_flats(client: TestClient) -> None:
    """flat_ids verilmezse tüm aktif dairelere borç oluşturulmalı."""
    token, site_id, flat_ids = _setup(client, "bulk-all@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    resp = client.post(
        "/api/v1/charges/bulk",
        json={
            "charge_type": "aidat",
            "period": "2026-08",
            "amount": "1500.00",
            "due_date": "2026-08-15",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 3
    assert data["skipped"] == 0
    assert data["errors"] == []


def test_bulk_charge_partial_flat_ids(client: TestClient) -> None:
    """Sadece belirtilen dairelere borç oluşturulmalı."""
    token, site_id, flat_ids = _setup(client, "bulk-partial@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    resp = client.post(
        "/api/v1/charges/bulk",
        json={
            "flat_ids": [flat_ids[0], flat_ids[1]],
            "charge_type": "elektrik",
            "period": "2026-08",
            "amount": "300.00",
            "due_date": "2026-08-20",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 2
    assert data["skipped"] == 0


def test_bulk_charge_skip_duplicates(client: TestClient) -> None:
    """Aynı flat+period+type için duplicate borçlar skipped sayılmalı."""
    token, site_id, flat_ids = _setup(client, "bulk-skip@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    payload = {
        "charge_type": "su",
        "period": "2026-09",
        "amount": "100.00",
        "due_date": "2026-09-10",
    }
    # İlk çağrı: 3 tane oluşturulmalı
    r1 = client.post("/api/v1/charges/bulk", json=payload, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["created"] == 3

    # Aynı payload tekrar: hepsi skip olmalı
    r2 = client.post("/api/v1/charges/bulk", json=payload, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["created"] == 0
    assert r2.json()["skipped"] == 3


def test_bulk_charge_unknown_flat_id(client: TestClient) -> None:
    """Geçersiz flat_id errors listesine düşmeli, diğerleri oluşturulmalı."""
    token, site_id, flat_ids = _setup(client, "bulk-err@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    resp = client.post(
        "/api/v1/charges/bulk",
        json={
            "flat_ids": [flat_ids[0], "nonexistent-uuid"],
            "charge_type": "aidat",
            "period": "2026-10",
            "amount": "500.00",
            "due_date": "2026-10-05",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 1
    assert len(data["errors"]) == 1


def test_bulk_charge_tenant_isolation(client: TestClient) -> None:
    """Bir sitenin bulk borcu diğer sitenin dairelerini etkilememeli."""
    token1, site_id1, flat_ids1 = _setup(client, "bulk-tenant1@example.com")
    token2, site_id2, flat_ids2 = _setup(client, "bulk-tenant2@example.com")

    headers1 = {"Authorization": f"Bearer {token1}", "X-Site-Id": site_id1}

    resp = client.post(
        "/api/v1/charges/bulk",
        json={"charge_type": "aidat", "period": "2026-11", "amount": "800.00", "due_date": "2026-11-10"},
        headers=headers1,
    )
    assert resp.status_code == 200
    assert resp.json()["created"] == 3

    # Site 2'nin daireleri etkilenmemeli
    headers2 = {"Authorization": f"Bearer {token2}", "X-Site-Id": site_id2}
    charges2 = client.get("/api/v1/charges?period=2026-11", headers=headers2).json()
    assert len(charges2) == 0


# ---------------------------------------------------------------------------
# Scheduled charge tests
# ---------------------------------------------------------------------------

def test_scheduled_charge_crud(client: TestClient) -> None:
    """ScheduledCharge oluştur / listele / güncelle / sil."""
    token, site_id, _ = _setup(client, "sc-crud@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    # Oluştur
    create_resp = client.post(
        "/api/v1/scheduled-charges",
        json={"charge_type": "aidat", "amount": "1500.00", "day_of_month": 5},
        headers=headers,
    )
    assert create_resp.status_code == 201
    sc_id = create_resp.json()["id"]
    assert create_resp.json()["charge_type"] == "aidat"

    # Listele
    list_resp = client.get("/api/v1/scheduled-charges", headers=headers)
    assert list_resp.status_code == 200
    assert any(item["id"] == sc_id for item in list_resp.json())

    # Güncelle
    patch_resp = client.patch(
        f"/api/v1/scheduled-charges/{sc_id}",
        json={"amount": "2000.00"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["amount"] == "2000.00"

    # Sil
    del_resp = client.delete(f"/api/v1/scheduled-charges/{sc_id}", headers=headers)
    assert del_resp.status_code == 204

    # Silinmiş kayıt görünmemeli
    get_resp = client.get(f"/api/v1/scheduled-charges/{sc_id}", headers=headers)
    assert get_resp.status_code == 404


def test_scheduled_charge_run(client: TestClient) -> None:
    """Run endpoint'i çağrıldığında tüm aktif dairelere borç üretmeli."""
    token, site_id, flat_ids = _setup(client, "sc-run@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    sc_id = client.post(
        "/api/v1/scheduled-charges",
        json={"charge_type": "aidat", "amount": "1200.00", "day_of_month": 10},
        headers=headers,
    ).json()["id"]

    run_resp = client.post(f"/api/v1/scheduled-charges/{sc_id}/run", headers=headers)
    assert run_resp.status_code == 200
    data = run_resp.json()
    assert data["created"] == 3
    assert data["skipped"] == 0

    # İkinci kez çalıştırınca hepsi skip olmalı
    run2 = client.post(f"/api/v1/scheduled-charges/{sc_id}/run", headers=headers)
    assert run2.json()["skipped"] == 3
    assert run2.json()["created"] == 0


def test_scheduled_charge_run_all(client: TestClient) -> None:
    """run-all tüm aktif kuralları çalıştırmalı, pasif olanları atlamalı."""
    token, site_id, _ = _setup(client, "sc-runall@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    # İki aktif, bir pasif kural
    client.post(
        "/api/v1/scheduled-charges",
        json={"charge_type": "aidat", "amount": "1000.00", "day_of_month": 5, "active": True},
        headers=headers,
    )
    client.post(
        "/api/v1/scheduled-charges",
        json={"charge_type": "elektrik", "amount": "200.00", "day_of_month": 5, "active": True},
        headers=headers,
    )
    client.post(
        "/api/v1/scheduled-charges",
        json={"charge_type": "su", "amount": "50.00", "day_of_month": 5, "active": False},
        headers=headers,
    )

    run_resp = client.post("/api/v1/scheduled-charges/run-all", headers=headers)
    assert run_resp.status_code == 200
    results = run_resp.json()
    # Sadece 2 aktif kural çalışmalı
    assert len(results) == 2
    total_created = sum(r["created"] for r in results)
    assert total_created == 6  # 2 kural × 3 daire
