from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    site_name = f"Taksit Site {email}"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "site_name": site_name,
            "full_name": "Admin",
            "email": email,
            "password": "StrongPass123",
        },
    )
    assert resp.status_code == 201
    site_id = resp.json()["site_id"]
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123"},
    )
    assert login.status_code == 200
    return login.json()["access_token"], site_id


def _setup_flat(client: TestClient, headers: dict) -> str:
    block = client.post("/api/v1/blocks", json={"name": "T Blok", "code": "T"}, headers=headers)
    assert block.status_code == 201
    flat = client.post(
        "/api/v1/flats",
        json={"block_id": block.json()["id"], "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert flat.status_code == 201
    return flat.json()["id"]


def test_installment_plan_create_and_list(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "install-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}
    flat_id = _setup_flat(client, headers)

    payload = {
        "flat_id": flat_id,
        "title": "2025 Aidat Taksiti",
        "total_amount": 1200.0,
        "installment_count": 4,
        "first_due_date": "2025-01-01",
    }
    create_resp = client.post("/api/v1/installments", json=payload, headers=headers)
    assert create_resp.status_code == 201
    plan = create_resp.json()
    assert plan["title"] == "2025 Aidat Taksiti"
    assert plan["installment_count"] == 4
    assert len(plan["items"]) == 4
    # Her taksit 300 TL
    for item in plan["items"]:
        assert float(item["amount"]) == 300.0

    list_resp = client.get("/api/v1/installments", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_installment_plan_detail(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "install-detail@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}
    flat_id = _setup_flat(client, headers)

    create = client.post(
        "/api/v1/installments",
        json={"flat_id": flat_id, "title": "Test", "total_amount": 600.0, "installment_count": 3, "first_due_date": "2025-03-01"},
        headers=headers,
    )
    plan_id = create.json()["id"]

    detail = client.get(f"/api/v1/installments/{plan_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == plan_id
    assert len(detail.json()["items"]) == 3


def test_installment_pay_item(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "install-pay@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}
    flat_id = _setup_flat(client, headers)

    plan = client.post(
        "/api/v1/installments",
        json={"flat_id": flat_id, "title": "Ödeme Testi", "total_amount": 500.0, "installment_count": 2, "first_due_date": "2025-06-01"},
        headers=headers,
    ).json()
    plan_id = plan["id"]
    item_id = plan["items"][0]["id"]

    pay_resp = client.patch(f"/api/v1/installments/{plan_id}/items/{item_id}/pay", headers=headers)
    assert pay_resp.status_code == 200
    assert pay_resp.json()["status"] == "paid"
    assert pay_resp.json()["paid_at"] is not None

    # Tekrar ödeme hata vermeli
    repeat = client.patch(f"/api/v1/installments/{plan_id}/items/{item_id}/pay", headers=headers)
    assert repeat.status_code == 409


def test_installment_delete(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "install-del@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}
    flat_id = _setup_flat(client, headers)

    plan_resp = client.post(
        "/api/v1/installments",
        json={"flat_id": flat_id, "title": "Silinecek", "total_amount": 100.0, "installment_count": 2, "first_due_date": "2025-07-01"},
        headers=headers,
    )
    assert plan_resp.status_code == 201, plan_resp.text
    plan = plan_resp.json()
    plan_id = plan["id"]

    del_resp = client.delete(f"/api/v1/installments/{plan_id}", headers=headers)
    assert del_resp.status_code == 204

    detail = client.get(f"/api/v1/installments/{plan_id}", headers=headers)
    assert detail.status_code == 404


def test_installment_tenant_isolation(client: TestClient) -> None:
    token_a, site_a = _register_and_login(client, "install-tenant-a@example.com")
    token_b, site_b = _register_and_login(client, "install-tenant-b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Site-Id": site_a}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Site-Id": site_b}

    flat_a = _setup_flat(client, headers_a)
    plan = client.post(
        "/api/v1/installments",
        json={"flat_id": flat_a, "title": "A Sitesi", "total_amount": 300.0, "installment_count": 3, "first_due_date": "2025-01-01"},
        headers=headers_a,
    ).json()
    plan_id = plan["id"]

    # B tenant plan A'ya erişememeli
    resp = client.get(f"/api/v1/installments/{plan_id}", headers=headers_b)
    assert resp.status_code == 404

    # B'nin listesi boş
    list_b = client.get("/api/v1/installments", headers=headers_b)
    assert list_b.json() == []
