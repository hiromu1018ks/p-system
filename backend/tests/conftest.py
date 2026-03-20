import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from models.user import User
from models.audit_log import AuditLog  # ensure table is created
from models.property_history import PropertyHistory  # ensure table is created
from models.property import Property  # ensure table is created
from models.file import File  # ensure table is created
from models.permission import Permission  # ensure table is created
from models.permission_history import PermissionHistory  # ensure table is created
from models.fee_detail import FeeDetail  # ensure table is created
from models.unit_price import UnitPrice  # ensure table is created
from models.jwt_blacklist import JWTBlacklist  # ensure table is created
from models.lease import Lease  # ensure table is created
from models.lease_history import LeaseHistory  # ensure table is created
from auth import hash_password, create_access_token


SQLALCHEMY_TEST_URL = "sqlite:///./test_zaisan.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """各テスト関数でクリーンなDBセッションを提供する"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    from main import app
    from database import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, db_session):
    """認証済みクライアント（staff権限）を提供する"""
    user = User(
        username="tanaka",
        hashed_password=hash_password("Password1"),
        display_name="田中太郎",
        role="staff",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id, user.username, user.role)
    client.headers["Authorization"] = f"Bearer {token}"
    client.user = user

    yield client


@pytest.fixture
def admin_client(client, db_session):
    """認証済みクライアント（admin権限）を提供する"""
    user = User(
        username="admin",
        hashed_password=hash_password("Admin123"),
        display_name="管理者",
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id, user.username, user.role)
    client.headers["Authorization"] = f"Bearer {token}"
    client.user = user

    yield client
