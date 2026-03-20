from models.user import User


def test_list_users_admin_only(admin_client, auth_client):
    resp = admin_client.get("/api/auth/users")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1

    resp = auth_client.get("/api/auth/users")
    assert resp.status_code == 403


def test_list_users_viewer_denied(viewer_client):
    resp = viewer_client.get("/api/auth/users")
    assert resp.status_code == 403


def test_unlock_user(admin_client, auth_client, db_session):
    user = db_session.query(User).filter_by(username="tanaka").first()
    user.is_locked = True
    db_session.commit()

    resp = admin_client.post(f"/api/auth/users/{user.id}/unlock")
    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.is_locked is False
    assert user.failed_login_count == 0


def test_create_user(admin_client):
    resp = admin_client.post("/api/auth/users", json={
        "username": "newuser",
        "password": "NewUser123",
        "display_name": "新規ユーザー",
        "role": "staff",
        "department": "テスト課"
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["username"] == "newuser"


def test_create_user_duplicate_username(admin_client):
    resp = admin_client.post("/api/auth/users", json={
        "username": "admin",
        "password": "NewUser123",
        "display_name": "Dup",
        "role": "staff",
    })
    assert resp.status_code == 400


def test_create_user_invalid_password(admin_client):
    resp = admin_client.post("/api/auth/users", json={
        "username": "badpass",
        "password": "short",
        "display_name": "Bad",
        "role": "staff",
    })
    assert resp.status_code == 422
