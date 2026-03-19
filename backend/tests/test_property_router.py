import pytest
from models.property import Property


class TestCreateProperty:
    def test_create_property_success(self, auth_client):
        resp = auth_client.post("/api/properties", json={
            "name": "市民公園",
            "property_type": "administrative",
            "address": "〇〇市〇〇町1-1",
            "lot_number": "1-1-1",
            "land_category": "宅地",
            "area_sqm": 1500.50,
            "latitude": 35.6812,
            "longitude": 139.7671,
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["property_code"].startswith("P")
        assert data["name"] == "市民公園"
        assert data["property_type"] == "administrative"

    def test_create_property_auto_code(self, auth_client):
        resp1 = auth_client.post("/api/properties", json={
            "name": "財産1", "property_type": "general",
        })
        resp2 = auth_client.post("/api/properties", json={
            "name": "財産2", "property_type": "general",
        })
        code1 = resp1.json()["data"]["property_code"]
        code2 = resp2.json()["data"]["property_code"]
        assert code1 != code2

    def test_create_property_invalid_type(self, auth_client):
        resp = auth_client.post("/api/properties", json={
            "name": "テスト", "property_type": "invalid",
        })
        assert resp.status_code == 422

    def test_create_property_negative_area(self, auth_client):
        resp = auth_client.post("/api/properties", json={
            "name": "テスト", "property_type": "administrative", "area_sqm": -100,
        })
        assert resp.status_code == 422

    def test_create_property_unauthenticated(self, client):
        resp = client.post("/api/properties", json={
            "name": "テスト", "property_type": "administrative",
        })
        assert resp.status_code == 401


class TestListProperties:
    def test_list_properties(self, auth_client):
        auth_client.post("/api/properties", json={"name": "公園A", "property_type": "administrative"})
        auth_client.post("/api/properties", json={"name": "公園B", "property_type": "general"})
        resp = auth_client.get("/api/properties")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_properties_filter_by_type(self, auth_client):
        auth_client.post("/api/properties", json={"name": "行政財産", "property_type": "administrative"})
        auth_client.post("/api/properties", json={"name": "普通財産", "property_type": "general"})
        resp = auth_client.get("/api/properties", params={"type": "administrative"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1

    def test_list_properties_search(self, auth_client):
        auth_client.post("/api/properties", json={"name": "中央公園", "property_type": "administrative", "address": "〇〇市中央"})
        auth_client.post("/api/properties", json={"name": "東公園", "property_type": "administrative", "address": "〇〇市東"})
        resp = auth_client.get("/api/properties", params={"q": "中央"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1

    def test_list_properties_pagination(self, auth_client):
        for i in range(25):
            auth_client.post("/api/properties", json={"name": f"財産{i}", "property_type": "general"})
        resp = auth_client.get("/api/properties", params={"page": 1, "per_page": 10})
        data = resp.json()["data"]
        assert data["total"] == 25
        assert len(data["items"]) == 10
        assert data["total_pages"] == 3

    def test_list_excludes_deleted(self, auth_client):
        auth_client.post("/api/properties", json={"name": "表示される", "property_type": "administrative"})
        props = auth_client.get("/api/properties").json()["data"]["items"]
        prop_id = props[0]["id"]
        auth_client.delete(f"/api/properties/{prop_id}")
        resp = auth_client.get("/api/properties")
        assert resp.json()["data"]["total"] == 0


class TestGetProperty:
    def test_get_property_success(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={"name": "テスト財産", "property_type": "administrative"})
        prop_id = create_resp.json()["data"]["id"]
        resp = auth_client.get(f"/api/properties/{prop_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "テスト財産"

    def test_get_property_not_found(self, auth_client):
        resp = auth_client.get("/api/properties/9999")
        assert resp.status_code == 404


class TestUpdateProperty:
    def test_update_property_success(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={"name": "旧名称", "property_type": "administrative"})
        prop_id = create_resp.json()["data"]["id"]
        resp = auth_client.put(f"/api/properties/{prop_id}", json={"name": "新名称", "remarks": "備考テスト"})
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "新名称"
        assert resp.json()["data"]["remarks"] == "備考テスト"

    def test_update_property_not_found(self, auth_client):
        resp = auth_client.put("/api/properties/9999", json={"name": "更新"})
        assert resp.status_code == 404


class TestDeleteProperty:
    def test_delete_property_success(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={"name": "削除対象", "property_type": "administrative"})
        prop_id = create_resp.json()["data"]["id"]
        resp = auth_client.delete(f"/api/properties/{prop_id}")
        assert resp.status_code == 200
        list_resp = auth_client.get("/api/properties")
        assert list_resp.json()["data"]["total"] == 0

    def test_delete_property_not_found(self, auth_client):
        resp = auth_client.delete("/api/properties/9999")
        assert resp.status_code == 404


class TestGetPropertyHistory:
    def test_get_history(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={"name": "テスト", "property_type": "administrative"})
        prop_id = create_resp.json()["data"]["id"]
        auth_client.put(f"/api/properties/{prop_id}", json={"name": "更新後"})
        resp = auth_client.get(f"/api/properties/{prop_id}/history")
        assert resp.status_code == 200
        history = resp.json()["data"]
        assert len(history) == 2  # CREATE + UPDATE
        assert history[0]["operation_type"] == "UPDATE"
        assert history[1]["operation_type"] == "CREATE"
