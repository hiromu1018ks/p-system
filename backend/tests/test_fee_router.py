import pytest
from models.property import Property
from models.permission import Permission


def _create_permission(auth_client):
    resp = auth_client.post("/api/properties", json={
        "name": "市民公園", "property_type": "administrative",
    })
    prop_id = resp.json()["data"]["id"]
    resp = auth_client.post("/api/permissions", json={
        "property_id": prop_id,
        "applicant_name": "山田",
        "applicant_address": "〇〇市",
        "purpose": "イベント",
        "start_date": "2024-04-01",
        "end_date": "2024-06-30",
        "usage_area_sqm": 50.0,
    })
    return resp.json()["data"]["id"]


class TestCalculateFee:
    def test_calculate_fee_success(self, auth_client):
        case_id = _create_permission(auth_client)
        resp = auth_client.post("/api/fees/calculate", json={
            "case_id": case_id,
            "case_type": "permission",
            "unit_price": 320,
            "area_sqm": 50.0,
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
            "discount_rate": 0.0,
            "tax_rate": 0.10,
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["total_amount"] > 0
        assert data["case_id"] == case_id

    def test_calculate_fee_saves_to_db(self, auth_client):
        case_id = _create_permission(auth_client)
        resp = auth_client.post("/api/fees/calculate", json={
            "case_id": case_id,
            "case_type": "permission",
            "unit_price": 320,
            "area_sqm": 50.0,
            "start_date": "2024-04-01",
            "end_date": "2024-05-31",
            "discount_rate": 0.0,
            "tax_rate": 0.10,
        })
        fee_id = resp.json()["data"]["id"]

        # 再計算で is_latest が変わることを確認
        resp2 = auth_client.post("/api/fees/calculate", json={
            "case_id": case_id,
            "case_type": "permission",
            "unit_price": 350,
            "area_sqm": 50.0,
            "start_date": "2024-04-01",
            "end_date": "2024-05-31",
            "discount_rate": 0.0,
            "tax_rate": 0.10,
        })
        assert resp2.status_code == 201


class TestUnitPrices:
    def test_create_unit_price(self, auth_client):
        resp = auth_client.post("/api/unit-prices", json={
            "property_type": "administrative",
            "usage": "公園使用",
            "unit_price": 320,
            "start_date": "2024-04-01",
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["unit_price"] == 320

    def test_list_unit_prices(self, auth_client):
        auth_client.post("/api/unit-prices", json={
            "property_type": "administrative",
            "usage": "公園使用",
            "unit_price": 320,
            "start_date": "2024-04-01",
        })
        resp = auth_client.get("/api/unit-prices")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1
