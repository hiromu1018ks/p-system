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
from models.document import Document  # ensure table is created
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


def _make_authenticated_client(db_session, username, password, display_name, role):
    """認証済みクライアントを作成するヘルパー"""
    from main import app
    from database import get_db
    from fastapi.testclient import TestClient

    user = User(
        username=username,
        hashed_password=hash_password(password),
        display_name=display_name,
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id, user.username, user.role)

    app.dependency_overrides[get_db] = lambda: db_session
    c = TestClient(app)
    c.headers["Authorization"] = f"Bearer {token}"
    c.user = user
    return c


@pytest.fixture
def auth_client(db_session):
    """認証済みクライアント（staff権限）を提供する"""
    yield _make_authenticated_client(
        db_session, "tanaka", "Password1", "田中太郎", "staff"
    )


@pytest.fixture
def viewer_client(db_session):
    """認証済みクライアント（viewer権限）を提供する"""
    yield _make_authenticated_client(
        db_session, "sato", "Sato12345", "佐藤花子", "viewer"
    )


@pytest.fixture
def admin_client(db_session):
    """認証済みクライアント（admin権限）を提供する"""
    yield _make_authenticated_client(
        db_session, "admin", "Admin123", "管理者", "admin"
    )
