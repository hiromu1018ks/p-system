import pytest
import io
from models.file import File


class TestUploadFile:
    def test_upload_file_success(self, auth_client):
        # 先に財産を作成
        create_resp = auth_client.post("/api/properties", json={
            "name": "テスト財産", "property_type": "administrative",
        })
        prop_id = create_resp.json()["data"]["id"]

        content = b"test file content"
        upload_file = io.BytesIO(content)
        upload_file.name = "test_document.pdf"

        resp = auth_client.post(
            "/api/files/upload",
            data={"related_type": "property", "related_id": str(prop_id), "file_type": "other"},
            files={"file": ("test_document.pdf", upload_file, "application/pdf")},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["original_filename"] == "test_document.pdf"
        assert data["related_type"] == "property"
        assert data["related_id"] == prop_id

    def test_upload_file_unauthenticated(self, client):
        resp = client.post("/api/files/upload")
        assert resp.status_code == 401

    def test_upload_file_related_entity_not_found(self, auth_client):
        upload_file = io.BytesIO(b"test")
        resp = auth_client.post(
            "/api/files/upload",
            data={"related_type": "property", "related_id": "9999", "file_type": "other"},
            files={"file": ("test.txt", upload_file, "text/plain")},
        )
        assert resp.status_code == 404

    def test_upload_file_missing_related_type(self, auth_client):
        upload_file = io.BytesIO(b"test")
        resp = auth_client.post(
            "/api/files/upload",
            data={"related_id": "1", "file_type": "other"},
            files={"file": ("test.txt", upload_file, "text/plain")},
        )
        assert resp.status_code == 422


class TestListFiles:
    def test_list_files_by_property(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={
            "name": "テスト財産", "property_type": "administrative",
        })
        prop_id = create_resp.json()["data"]["id"]

        upload_file = io.BytesIO(b"test content")
        auth_client.post(
            "/api/files/upload",
            data={"related_type": "property", "related_id": str(prop_id), "file_type": "photo"},
            files={"file": ("photo.jpg", upload_file, "image/jpeg")},
        )

        resp = auth_client.get("/api/files", params={"related_type": "property", "related_id": prop_id})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["original_filename"] == "photo.jpg"


class TestDownloadFile:
    def test_download_file_success(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={
            "name": "テスト財産", "property_type": "administrative",
        })
        prop_id = create_resp.json()["data"]["id"]

        content = b"download test content"
        upload_file = io.BytesIO(content)
        upload_resp = auth_client.post(
            "/api/files/upload",
            data={"related_type": "property", "related_id": str(prop_id), "file_type": "other"},
            files={"file": ("download_test.txt", upload_file, "text/plain")},
        )
        file_id = upload_resp.json()["data"]["id"]

        resp = auth_client.get(f"/api/files/{file_id}/download")
        assert resp.status_code == 200
        assert resp.content == content

    def test_download_file_not_found(self, auth_client):
        resp = auth_client.get("/api/files/9999/download")
        assert resp.status_code == 404


class TestDeleteFile:
    def test_delete_file_success(self, auth_client):
        create_resp = auth_client.post("/api/properties", json={
            "name": "テスト財産", "property_type": "administrative",
        })
        prop_id = create_resp.json()["data"]["id"]

        upload_file = io.BytesIO(b"delete test")
        upload_resp = auth_client.post(
            "/api/files/upload",
            data={"related_type": "property", "related_id": str(prop_id), "file_type": "other"},
            files={"file": ("delete_test.txt", upload_file, "text/plain")},
        )
        file_id = upload_resp.json()["data"]["id"]

        resp = auth_client.delete(f"/api/files/{file_id}")
        assert resp.status_code == 200

        list_resp = auth_client.get("/api/files", params={"related_type": "property", "related_id": prop_id})
        assert len(list_resp.json()["data"]) == 0
