import pytest
from sqlalchemy import text
from models.user import User


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
