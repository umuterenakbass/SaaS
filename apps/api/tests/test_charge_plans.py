from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> tuple[str, str]:
    register_payload = {
        "site_name": "Plan Site",
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


def test_charge_plan_crud_and_assignment_guards(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "plan-admin@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "P Blok", "code": "P"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    flat_resp = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "101", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert flat_resp.status_code == 201
    flat_id = flat_resp.json()["id"]

    create_plan_resp = client.post(
        "/api/v1/charge-plans",
        json={
            "name": "Aylık Aidat",
            "charge_type": "aidat",
            "amount": "1200.00",
            "frequency": "monthly",
            "start_period": "2026-05",
            "end_period": None,
            "is_active": True,
        },
        headers=headers,
    )
    assert create_plan_resp.status_code == 201
    plan_id = create_plan_resp.json()["id"]

    list_plans_resp = client.get("/api/v1/charge-plans?is_active=true", headers=headers)
    assert list_plans_resp.status_code == 200
    assert len(list_plans_resp.json()) == 1

    update_plan_resp = client.patch(
        f"/api/v1/charge-plans/{plan_id}",
        json={"amount": "1300.00", "name": "Aylık Aidat Güncel"},
        headers=headers,
    )
    assert update_plan_resp.status_code == 200
    assert update_plan_resp.json()["amount"] == "1300.00"

    create_assignment_resp = client.post(
        f"/api/v1/charge-plans/{plan_id}/assignments",
        json={"flat_id": flat_id},
        headers=headers,
    )
    assert create_assignment_resp.status_code == 201
    assignment_id = create_assignment_resp.json()["id"]

    duplicate_assignment_resp = client.post(
        f"/api/v1/charge-plans/{plan_id}/assignments",
        json={"flat_id": flat_id},
        headers=headers,
    )
    assert duplicate_assignment_resp.status_code == 409

    list_assignments_resp = client.get(f"/api/v1/charge-plans/{plan_id}/assignments", headers=headers)
    assert list_assignments_resp.status_code == 200
    assert len(list_assignments_resp.json()) == 1

    wrong_tenant_resp = client.get(
        "/api/v1/charge-plans",
        headers={"Authorization": f"Bearer {token}", "X-Site-Id": "wrong-site"},
    )
    assert wrong_tenant_resp.status_code == 403

    delete_assignment_resp = client.delete(
        f"/api/v1/charge-plans/{plan_id}/assignments/{assignment_id}",
        headers=headers,
    )
    assert delete_assignment_resp.status_code == 204

    delete_plan_resp = client.delete(f"/api/v1/charge-plans/{plan_id}", headers=headers)
    assert delete_plan_resp.status_code == 204


def test_charge_plan_generate_idempotent_and_period_rules(client: TestClient) -> None:
    token, site_id = _register_and_login(client, "plan-generate@example.com")
    headers = {"Authorization": f"Bearer {token}", "X-Site-Id": site_id}

    block_resp = client.post(
        "/api/v1/blocks",
        json={"name": "G Blok", "code": "G"},
        headers=headers,
    )
    assert block_resp.status_code == 201
    block_id = block_resp.json()["id"]

    flat_one = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "1", "floor": 1, "status": "active"},
        headers=headers,
    )
    flat_two = client.post(
        "/api/v1/flats",
        json={"block_id": block_id, "unit_no": "2", "floor": 1, "status": "active"},
        headers=headers,
    )
    assert flat_one.status_code == 201
    assert flat_two.status_code == 201

    create_plan_resp = client.post(
        "/api/v1/charge-plans",
        json={
            "name": "Yıllık Aidat Planı",
            "charge_type": "aidat",
            "amount": "1000.00",
            "frequency": "monthly",
            "start_period": "2026-05",
            "end_period": "2026-12",
            "is_active": True,
        },
        headers=headers,
    )
    assert create_plan_resp.status_code == 201
    plan_id = create_plan_resp.json()["id"]

    assign_one = client.post(
        f"/api/v1/charge-plans/{plan_id}/assignments",
        json={"flat_id": flat_one.json()["id"]},
        headers=headers,
    )
    assign_two = client.post(
        f"/api/v1/charge-plans/{plan_id}/assignments",
        json={"flat_id": flat_two.json()["id"]},
        headers=headers,
    )
    assert assign_one.status_code == 201
    assert assign_two.status_code == 201

    first_generate = client.post(
        f"/api/v1/charge-plans/{plan_id}/generate",
        json={"period": "2026-06", "due_date": "2026-06-15", "status": "pending"},
        headers=headers,
    )
    assert first_generate.status_code == 200
    assert first_generate.json()["requested_assignments"] == 2
    assert first_generate.json()["created_count"] == 2
    assert first_generate.json()["skipped_count"] == 0

    second_generate = client.post(
        f"/api/v1/charge-plans/{plan_id}/generate",
        json={"period": "2026-06", "due_date": "2026-06-15", "status": "pending"},
        headers=headers,
    )
    assert second_generate.status_code == 200
    assert second_generate.json()["created_count"] == 0
    assert second_generate.json()["skipped_count"] == 2

    before_period = client.post(
        f"/api/v1/charge-plans/{plan_id}/generate",
        json={"period": "2026-04", "due_date": "2026-04-15", "status": "pending"},
        headers=headers,
    )
    assert before_period.status_code == 400

    after_period = client.post(
        f"/api/v1/charge-plans/{plan_id}/generate",
        json={"period": "2027-01", "due_date": "2027-01-15", "status": "pending"},
        headers=headers,
    )
    assert after_period.status_code == 400
