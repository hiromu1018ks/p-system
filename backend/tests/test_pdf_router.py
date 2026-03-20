import pytest
from models.property import Property


def _create_property(auth_client, property_type="administrative"):
    resp = auth_client.post("/api/properties", json={
        "name": "テスト財産",
        "property_type": property_type,
    })
    return resp.json()["data"]["id"]


def _create_permission(auth_client, prop_id, status="approved"):
    resp = auth_client.post("/api/permissions", json={
        "property_id": prop_id,
        "applicant_name": "山田",
        "applicant_address": "〇〇市",
        "purpose": "テスト",
        "start_date": "2024-04-01",
        "end_date": "2024-06-30",
    })
    perm = resp.json()["data"]
    for next_status in ["submitted", "under_review", "pending_approval", "approved"]:
        resp2 = auth_client.post(f"/api/permissions/{perm['id']}/status", json={
            "new_status": next_status,
            "reason": "テスト",
            "expected_current_status": perm["status"],
            "expected_updated_at": perm["updated_at"],
        })
        perm = resp2.json()["data"]
    return perm


def _create_lease(admin_client, prop_id, status="active"):
    resp = admin_client.post("/api/leases", json={
        "property_id": prop_id,
        "property_sub_type": "land",
        "lessee_name": "山田商事",
        "lessee_address": "〇〇市",
        "purpose": "テスト",
        "start_date": "2024-04-01",
        "end_date": "2025-03-31",
    })
    lease = resp.json()["data"]
    for next_status in ["negotiating", "pending_approval", "active"]:
        resp2 = admin_client.post(f"/api/leases/{lease['id']}/status", json={
            "new_status": next_status,
            "reason": "テスト",
            "expected_current_status": lease["status"],
            "expected_updated_at": lease["updated_at"],
        })
        lease = resp2.json()["data"]
    return lease


class TestGeneratePermissionCertificate:
    def test_generate_permission_certificate(self, admin_client):
        prop_id = _create_property(admin_client)
        perm = _create_permission(admin_client, prop_id)

        resp = admin_client.post(f"/api/pdf/permission/{perm['id']}")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["document_type"] == "permission_certificate"
        assert data["file_path"] is not None

    def test_generate_not_approved(self, auth_client):
        prop_id = _create_property(auth_client)
        resp = auth_client.post("/api/permissions", json={
            "property_id": prop_id,
            "applicant_name": "山田",
            "applicant_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2024-06-30",
        })
        perm_id = resp.json()["data"]["id"]

        resp = auth_client.post(f"/api/pdf/permission/{perm_id}")
        assert resp.status_code == 409

    def test_generate_not_found(self, auth_client):
        resp = auth_client.post("/api/pdf/permission/9999")
        assert resp.status_code == 404


class TestGenerateLandLeaseContract:
    def test_generate_land_lease(self, admin_client):
        prop_id = _create_property(admin_client, "general")
        lease = _create_lease(admin_client, prop_id)

        resp = admin_client.post(f"/api/pdf/lease-land/{lease['id']}")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["document_type"] == "land_lease_contract"


class TestGenerateBuildingLeaseContract:
    def test_generate_building_lease(self, admin_client):
        prop_id = _create_property(admin_client, "general")
        resp = admin_client.post("/api/leases", json={
            "property_id": prop_id,
            "property_sub_type": "building",
            "lessee_name": "田中商店",
            "lessee_address": "〇〇市",
            "purpose": "テスト",
            "start_date": "2024-04-01",
            "end_date": "2025-03-31",
        })
        lease = resp.json()["data"]
        for next_status in ["negotiating", "pending_approval", "active"]:
            resp2 = admin_client.post(f"/api/leases/{lease['id']}/status", json={
                "new_status": next_status,
                "reason": "テスト",
                "expected_current_status": lease["status"],
                "expected_updated_at": lease["updated_at"],
            })
            lease = resp2.json()["data"]

        resp = admin_client.post(f"/api/pdf/lease-building/{lease['id']}")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["document_type"] == "building_lease_contract"


class TestGenerateRenewalNotice:
    def test_renewal_notice_permission(self, admin_client):
        prop_id = _create_property(admin_client)
        perm = _create_permission(admin_client, prop_id)

        resp = admin_client.post(f"/api/pdf/renewal/permission/{perm['id']}")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["document_type"] == "renewal_notice"

    def test_renewal_notice_lease(self, admin_client):
        prop_id = _create_property(admin_client, "general")
        lease = _create_lease(admin_client, prop_id)

        resp = admin_client.post(f"/api/pdf/renewal/lease/{lease['id']}")
        assert resp.status_code == 201


class TestDownloadPdf:
    def test_download_pdf(self, admin_client):
        prop_id = _create_property(admin_client)
        perm = _create_permission(admin_client, prop_id)

        gen = admin_client.post(f"/api/pdf/permission/{perm['id']}")
        doc = gen.json()["data"]
        doc_id = doc["id"]

        resp = admin_client.get(f"/api/pdf/download/{doc_id}")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 0

    def test_download_not_found(self, admin_client):
        resp = admin_client.get("/api/pdf/download/9999")
        assert resp.status_code == 404
