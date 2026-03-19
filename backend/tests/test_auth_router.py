import pytest
from models.user import User
from auth import hash_password


def _create_test_user(db_session, username="tanaka", password="Password1", role="staff"):
    user = User(
        username=username,
        hashed_password=hash_password(password),
        display_name="田中太郎",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestLogin:
    def test_login_success(self, client, db_session):
        _create_test_user(db_session)

        response = client.post("/api/auth/login", json={
            "username": "tanaka",
            "password": "Password1",
        })

        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "tanaka"
        assert data["user"]["role"] == "staff"

    def test_login_wrong_password(self, client, db_session):
        _create_test_user(db_session)

        response = client.post("/api/auth/login", json={
            "username": "tanaka",
            "password": "wrongPassword",
        })

        assert response.status_code == 401
        assert "error" in response.json()

    def test_login_user_not_found(self, client):
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "Password1",
        })

        assert response.status_code == 401

    def test_login_locked_account(self, client, db_session):
        _create_test_user(db_session)
        db_session.query(User).filter_by(username="tanaka").update({"is_locked": True})
        db_session.commit()

        response = client.post("/api/auth/login", json={
            "username": "tanaka",
            "password": "Password1",
        })

        assert response.status_code == 403
        assert "ロック" in response.json()["error"]["message"]

    def test_login_increments_failed_count(self, client, db_session):
        _create_test_user(db_session)

        for _ in range(4):
            client.post("/api/auth/login", json={
                "username": "tanaka",
                "password": "wrong",
            })

        user = db_session.query(User).filter_by(username="tanaka").first()
        assert user.failed_login_count == 4

    def test_login_locks_after_5_failures(self, client, db_session):
        _create_test_user(db_session)

        for _ in range(5):
            client.post("/api/auth/login", json={
                "username": "tanaka",
                "password": "wrong",
            })

        user = db_session.query(User).filter_by(username="tanaka").first()
        assert user.is_locked is True
        assert user.failed_login_count == 5

    def test_login_resets_failed_count_on_success(self, client, db_session):
        _create_test_user(db_session)
        db_session.query(User).filter_by(username="tanaka").update({"failed_login_count": 3})
        db_session.commit()
        client.post("/api/auth/login", json={
            "username": "tanaka",
            "password": "Password1",
        })

        user = db_session.query(User).filter_by(username="tanaka").first()
        assert user.failed_login_count == 0
