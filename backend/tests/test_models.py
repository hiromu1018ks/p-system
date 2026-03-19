import pytest
from datetime import datetime
from sqlalchemy import text
from models.user import User
from models.jwt_blacklist import JWTBlacklist
from models.audit_log import AuditLog


def test_user_table_exists(db_session):
    """m_user テーブルが存在し、カラムが正しいこと"""
    result = db_session.execute(text("PRAGMA table_info(m_user)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "username" in columns
    assert "hashed_password" in columns
    assert "display_name" in columns
    assert "role" in columns
    assert "is_locked" in columns
    assert "failed_login_count" in columns
    assert "is_deleted" in columns


def test_create_user(db_session):
    """User レコードを作成できること"""
    user = User(
        username="testuser",
        hashed_password="hashed_pw",
        display_name="テストユーザー",
        role="staff",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.role == "staff"
    assert user.is_locked is False
    assert user.is_deleted is False
    assert user.failed_login_count == 0


def test_user_default_values(db_session):
    """デフォルト値が正しく設定されること"""
    user = User(
        username="defaults",
        hashed_password="hashed",
        display_name="Default",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.role == "staff"
    assert user.is_locked is False
    assert user.is_deleted is False
    assert user.failed_login_count == 0


def test_jwt_blacklist_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_jwt_blacklist)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "token_jti" in columns
    assert "expires_at" in columns


def test_create_jwt_blacklist(db_session):
    entry = JWTBlacklist(
        token_jti="test-jti-123",
        expires_at=datetime(2026, 12, 31, 23, 59, 59),
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    assert entry.id is not None
    assert entry.token_jti == "test-jti-123"


def test_audit_log_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_audit_log)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "user_id" in columns
    assert "action" in columns
    assert "target_table" in columns
    assert "changed_fields" in columns
    assert "before_value" in columns
    assert "after_value" in columns


def test_create_audit_log(db_session):
    log = AuditLog(
        user_id=1,
        action="CREATE",
        target_table="m_user",
        target_id=1,
        changed_fields='["username", "display_name"]',
        before_value="null",
        after_value='{"username": "tanaka"}',
        ip_address="127.0.0.1",
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    assert log.id is not None
    assert log.action == "CREATE"
