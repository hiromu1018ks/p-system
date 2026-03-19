import pytest
from fastapi import Depends
from models.user import User
from models.jwt_blacklist import JWTBlacklist
from auth import hash_password, create_access_token, decode_access_token
from datetime import datetime, timezone


def _create_user(db_session, username="tanaka", role="staff"):
    user = User(
        username=username,
        hashed_password=hash_password("Password1"),
        display_name="田中太郎",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _blacklist_token(db_session, token):
    payload = decode_access_token(token)
    entry = JWTBlacklist(
        token_jti=payload["jti"],
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )
    db_session.add(entry)
    db_session.commit()


class TestGetCurrentUser:
    def test_valid_token(self, client, db_session):
        _create_user(db_session)

        login_resp = client.post("/api/auth/login", json={
            "username": "tanaka", "password": "Password1"
        })
        token = login_resp.json()["data"]["access_token"]

        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "tanaka"

    def test_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_blacklisted_token(self, client, db_session):
        _create_user(db_session)

        login_resp = client.post("/api/auth/login", json={
            "username": "tanaka", "password": "Password1"
        })
        token = login_resp.json()["data"]["access_token"]

        _blacklist_token(db_session, token)

        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


class TestRequireRole:
    def test_admin_access(self, client, db_session):
        _create_user(db_session, username="admin_user", role="admin")

        login_resp = client.post("/api/auth/login", json={
            "username": "admin_user", "password": "Password1"
        })
        token = login_resp.json()["data"]["access_token"]

        resp = client.get("/api/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_staff_denied(self, client, db_session):
        _create_user(db_session, role="staff")

        login_resp = client.post("/api/auth/login", json={
            "username": "tanaka", "password": "Password1"
        })
        token = login_resp.json()["data"]["access_token"]

        resp = client.get("/api/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
