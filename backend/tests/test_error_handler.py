import pytest


class TestErrorResponseFormat:
    def test_404_response_format(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_422_validation_error_format(self, client):
        resp = client.post("/api/auth/login", json={"username": "tanaka"})
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body

    def test_health_success_format(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert body["message"] == "OK"
