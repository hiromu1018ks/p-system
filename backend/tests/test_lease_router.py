import pytest
from models.property import Property


def _create_property(auth_client):
    resp = auth_client.post("/api/properties", json={
        "name": "市有地",
        "property_type": "general",
        "address": "〇〇市〇〇町1-1",
    })
    return resp.json()["data"]["id"]


class TestCreateLease:
    def test_create_lease_success(self, auth_client):
        prop_id = _create_property(auth_client)
        resp = auth_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田商事",
            "lessee_address": "〇〇市1-1",
            "purpose": "事務所",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
            "leased_area": "100.00",
            "payment_method": "monthly",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "draft"
        assert data["lease_number"] is None
        assert data["lessee_name"] == "山田商事"

    def test_create_lease_invalid_sub_type(self, auth_client):
        prop_id = _create_property(auth_client)
        resp = auth_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "invalid",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        assert resp.status_code == 422

    def test_create_lease_property_not_found(self, auth_client):
        resp = auth_client.post("/api/leases", json={
            "property_id": 9999,
            "property_sub_type": "land",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        assert resp.status_code == 404


class TestListLeases:
    def test_list_leases(self, auth_client):
        prop_id = _create_property(auth_client)
        auth_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        resp = auth_client.get("/api/leases")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    def test_list_filter_by_status(self, auth_client):
        prop_id = _create_property(auth_client)
        auth_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "building",
            "lessee_name": "田中",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        resp = auth_client.get("/api/leases", params={"status": "draft"})
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["status"] == "draft"


class TestGetLease:
    def test_get_lease_success(self, auth_client):
        prop_id = _create_property(auth_client)
        create = auth_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        lease_id = create.json()["data"]["id"]
        resp = auth_client.get(f"/api/leases/{lease_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["lessee_name"] == "山田"

    def test_get_lease_not_found(self, auth_client):
        resp = auth_client.get("/api/leases/9999")
        assert resp.status_code == 404


class TestStatusChange:
    def test_draft_to_negotiating(self, auth_client):
        prop_id = _create_property(auth_client)
        create = auth_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        lease = create.json()["data"]
        resp = auth_client.post(f"/api/leases/{lease['id']}/status", json={
            "new_status": "negotiating",
            "reason": "協議開始",
            "expected_current_status": "draft",
            "expected_updated_at": lease["updated_at"],
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "negotiating"

    def test_full_flow_to_active(self, admin_client):
        """draft → negotiating → pending_approval → active の全フロー"""
        prop_id = _create_property(admin_client)
        create = admin_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田商事",
            "lessee_address": "〇〇市",
            "purpose": "事務所",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        lease = create.json()["data"]

        # draft → negotiating
        resp1 = admin_client.post(f"/api/leases/{lease['id']}/status", json={
            "new_status": "negotiating",
            "reason": "協議開始",
            "expected_current_status": "draft",
            "expected_updated_at": lease["updated_at"],
        })
        lease = resp1.json()["data"]

        # negotiating → pending_approval
        resp2 = admin_client.post(f"/api/leases/{lease['id']}/status", json={
            "new_status": "pending_approval",
            "reason": "決裁上申",
            "expected_current_status": "negotiating",
            "expected_updated_at": lease["updated_at"],
        })
        lease = resp2.json()["data"]

        # pending_approval → active（管理者のみ）
        resp3 = admin_client.post(f"/api/leases/{lease['id']}/status", json={
            "new_status": "active",
            "reason": "決裁完了",
            "expected_current_status": "pending_approval",
            "expected_updated_at": lease["updated_at"],
        })
        assert resp3.status_code == 200
        data = resp3.json()["data"]
        assert data["status"] == "active"
        assert data["lease_number"] is not None  # active時に採番

    def test_invalid_transition(self, admin_client):
        prop_id = _create_property(admin_client)
        create = admin_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        lease = create.json()["data"]
        # draft → expired は直接不可
        resp = admin_client.post(f"/api/leases/{lease['id']}/status", json={
            "new_status": "expired",
            "reason": "テスト",
            "expected_current_status": "draft",
            "expected_updated_at": lease["updated_at"],
        })
        assert resp.status_code == 409


class TestRenewal:
    def test_start_renewal_from_active(self, admin_client):
        prop_id = _create_property(admin_client)
        create = admin_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "land",
            "lessee_name": "山田",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        lease = create.json()["data"]

        # draft → negotiating → pending_approval → active
        for status, reason in [
            ("negotiating", "協議"), ("pending_approval", "上申"),
            ("active", "決裁完了"),
        ]:
            resp = admin_client.post(f"/api/leases/{lease['id']}/status", json={
                "new_status": status,
                "reason": reason,
                "expected_current_status": lease["status"],
                "expected_updated_at": lease["updated_at"],
            })
            lease = resp.json()["data"]

        # 更新手続き開始
        resp = admin_client.post(f"/api/leases/{lease['id']}/renewal", json={
            "reason": "契約更新",
        })
        assert resp.status_code == 200
        new_lease = resp.json()["data"]
        assert new_lease["status"] == "draft"
        assert new_lease["parent_case_id"] == lease["id"]
        assert new_lease["renewal_seq"] == 1
        assert new_lease["is_latest_case"] is True
