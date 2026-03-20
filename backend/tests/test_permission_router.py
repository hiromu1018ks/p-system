import pytest
from models.property import Property
from models.permission import Permission


def _create_property(auth_client):
    resp = auth_client.post("/api/properties", json={
        "name": "市民公園",
        "property_type": "administrative",
        "address": "〇〇市〇〇町1-1",
    })
    return resp.json()["data"]["id"]


class TestCreatePermission:
    def test_create_permission_success(self, auth_client):
        prop_id = _create_property(auth_client)
        resp = auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田太郎",
            "applicant_address": "〇〇市1-1",
            "purpose": "イベント開催",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
            "usage_area_sqm": 50.0,
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "draft"
        assert data["permission_number"] is None
        assert data["applicant_name"] == "山田太郎"

    def test_create_permission_invalid_dates(self, auth_client):
        prop_id = _create_property(auth_client)
        resp = auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-06-30",
            "end_date": "2024-04-01",
        })
        assert resp.status_code == 422

    def test_create_permission_property_not_found(self, auth_client):
        resp = auth_client.post("/api/permissions", json={
            "property_id": 9999,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
        })
        assert resp.status_code == 404


class TestListPermissions:
    def test_list_permissions(self, auth_client):
        prop_id = _create_property(auth_client)
        auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "イベント",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
        })
        resp = auth_client.get("/api/permissions")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    def test_list_filter_by_status(self, auth_client):
        prop_id = _create_property(auth_client)
        auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
        })
        resp = auth_client.get("/api/permissions", params={"status": "draft"})
        assert resp.status_code == 200
        for item in resp.json()["data"]["items"]:
            assert item["status"] == "draft"


class TestGetPermission:
    def test_get_permission_success(self, auth_client):
        prop_id = _create_property(auth_client)
        create = auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
        })
        perm_id = create.json()["data"]["id"]
        resp = auth_client.get(f"/api/permissions/{perm_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["applicant_name"] == "山田"

    def test_get_permission_not_found(self, auth_client):
        resp = auth_client.get("/api/permissions/9999")
        assert resp.status_code == 404


class TestUpdatePermission:
    def test_update_permission_success(self, auth_client):
        prop_id = _create_property(auth_client)
        create = auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "旧目的",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
        })
        perm_id = create.json()["data"]["id"]
        resp = auth_client.put(f"/api/permissions/{perm_id}", json={
            "purpose": "新目的",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["purpose"] == "新目的"
