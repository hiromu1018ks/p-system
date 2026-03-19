import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base


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
