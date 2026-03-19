# 認証・共通基盤 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 自治体財産管理システムの基盤を構築する。JWT認証、ロール制御、監査ログ、ステータス遷移マシンを実装し、ログイン画面からフロントエンドへのアクセスまで動作する状態にする。

**Architecture:** バックエンドは FastAPI + SQLAlchemy 2.x + SQLite（WALモード）。認証は JWT（python-jose）+ bcrypt、ロールは staff/admin/viewer の3種。監査ログは全操作を before/after 付きで記録。ステータス遷移は設定駆動のステートマシンで検証。フロントエンドは React 18 + Vite + React Router v6。

**Tech Stack:** Python 3.11+, FastAPI 0.110+, SQLAlchemy 2.x, Alembic, python-jose, passlib, pytest, React 18, Vite 5, React Router 6

---

## ファイル構成

### 作成ファイル一覧

| ファイル | 責務 |
|---------|------|
| `backend/config.py` | 環境変数・アプリ設定（SECRET_KEY, DB_URL等） |
| `backend/database.py` | SQLAlchemy engine・sessionfactory・依存注入 |
| `backend/main.py` | FastAPI app定義・CORS・ルーター登録・エラーハンドラ |
| `backend/auth.py` | パスワードハッシュ・JWT生成/検証・パスワードポリシー |
| `backend/audit.py` | 監査ログ記録ユーティリティ |
| `backend/models/__init__.py` | モデルパッケージ初期化・Base import |
| `backend/models/user.py` | `m_user` テーブルモデル |
| `backend/models/jwt_blacklist.py` | `t_jwt_blacklist` テーブルモデル |
| `backend/models/audit_log.py` | `t_audit_log` テーブルモデル |
| `backend/schemas/__init__.py` | スキーマパッケージ初期化 |
| `backend/schemas/auth.py` | ログイン/ログアウトのリクエスト・レスポンス |
| `backend/schemas/common.py` | エラーレスポンス・ページング共通スキーマ |
| `backend/routers/__init__.py` | ルーターパッケージ初期化 |
| `backend/routers/auth.py` | `/api/auth/login`, `/api/auth/logout` エンドポイント |
| `backend/services/__init__.py` | サービスパッケージ初期化 |
| `backend/services/status_machine.py` | 使用許可・貸付のステータス遷移ルール |
| `backend/alembic.ini` | Alembic設定ファイル |
| `backend/alembic/env.py` | Alembicマイグレーション環境 |
| `backend/alembic/script.py.mako` | マイグレーションテンプレート |
| `backend/tests/__init__.py` | テストパッケージ初期化 |
| `backend/tests/conftest.py` | テストDB・session・client フィクスチャ |
| `backend/tests/test_auth_service.py` | auth.py の単体テスト |
| `backend/tests/test_auth_router.py` | ログイン/ログアウト API テスト |
| `backend/tests/test_audit.py` | 監査ログユーティリティテスト |
| `backend/tests/test_status_machine.py` | ステータス遷移テスト |
| `backend/tests/test_error_handler.py` | エラーレスポンス形式テスト |
| `backend/seed.py` | 初期管理者アカウント作成スクリプト |
| `backend/.env` | 開発用環境変数（git ignore対象） |
| `backend/.env.example` | 環境変数テンプレート |
| `backend/requirements.txt` | Python依存パッケージ |
| `frontend/package.json` | Node.js依存パッケージ |
| `frontend/vite.config.js` | Vite設定（APIプロキシ） |
| `frontend/index.html` | HTMLエントリポイント |
| `frontend/src/main.jsx` | Reactエントリ・Router設定 |
| `frontend/src/App.jsx` | ルートコンポーネント |
| `frontend/src/App.css` | グローバルスタイル |
| `frontend/src/api/client.js` | fetchラッパー（JWT付与・エラー処理） |
| `frontend/src/api/auth.js` | 認証API呼び出し |
| `frontend/src/contexts/AuthContext.jsx` | 認証状態管理 |
| `frontend/src/components/ProtectedRoute.jsx` | 認証ガードコンポーネント |
| `frontend/src/pages/Login.jsx` | ログイン画面 |
| `frontend/src/pages/DashboardPlaceholder.jsx` | ダッシュボード（仮） |

---

## Task 1: Backend プロジェクト構築

**Files:**
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`

- [ ] **Step 1: バックエンドディレクトリを作成**

```bash
mkdir -p backend/{models,schemas,routers,services,tests,templates,uploads,generated_pdfs,backups,alembic/versions}
```

- [ ] **Step 2: requirements.txt を作成**

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic[email]>=2.5.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
python-dotenv>=1.0.0
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 3: 依存パッケージをインストール**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Expected: 全パッケージがインストールされエラーなし

- [ ] **Step 4: `.env.example` を作成**

```env
SECRET_KEY=change-me-in-production
DATABASE_URL=sqlite:///./zaisan.db
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
MAX_LOGIN_ATTEMPTS=5
```

- [ ] **Step 5: `.env` を作成（dev用）**

```bash
cp .env.example .env
# .env の SECRET_KEY を開発用に設定（後でseed.pyで上書き可能）
```

`.env` の内容:
```env
SECRET_KEY=dev-secret-key-not-for-production
DATABASE_URL=sqlite:///./zaisan.db
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=8
MAX_LOGIN_ATTEMPTS=5
```

- [ ] **Step 6: `backend/config.py` を作成**

```python
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-not-for-production")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./zaisan.db")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "8"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))


settings = Settings()
```

- [ ] **Step 7: `backend/database.py` を作成**

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 8: `backend/main.py` を作成（最小構成）**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="自治体財産管理システム", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 9: バックエンド起動確認**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

別ターミナルで確認:
```bash
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 10: `.gitignore` に追加項目を記載（プロジェクトルート）**

```
backend/venv/
backend/__pycache__/
backend/**/__pycache__/
backend/zaisan.db
backend/.env
backend/uploads/*
backend/generated_pdfs/*
backend/backups/*
```

- [ ] **Step 11: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend project with FastAPI, SQLAlchemy, config"
```

---

## Task 2: User モデル + Alembic セットアップ + 初期マイグレーション

**Files:**
- Create: `backend/models/__init__.py`
- Create: `backend/models/user.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_models.py`:
```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
source venv/bin/activate
pytest tests/test_models.py -v
```

Expected: FAIL（User モデルが存在しない）

- [ ] **Step 3: `backend/models/__init__.py` を作成**

```python
from database import Base
```

- [ ] **Step 4: `backend/models/user.py` を作成**

```python
from datetime import datetime

from sqlalchemy import String, Boolean, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class User(Base):
    __tablename__ = "m_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="staff")
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Step 5: `backend/tests/__init__.py` を作成**

空ファイル。

- [ ] **Step 6: `backend/tests/conftest.py` を作成**

```python
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
```

- [ ] **Step 7: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_models.py -v
```

Expected: 3 passed

- [ ] **Step 8: Alembic を初期化**

```bash
cd backend
alembic init alembic
```

- [ ] **Step 9: `alembic.ini` を修正**

`sqlalchemy.url` 行をコメントアウトまたは削除（env.py で動的に設定するため）。

- [ ] **Step 10: `alembic/env.py` を修正**

```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from config import settings
from models import Base
import models.user  # noqa: F401 - モデルをBase.metadataに登録するため

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 11: 初期マイグレーションを生成・適用**

```bash
cd backend
alembic revision --autogenerate -m "create m_user table"
alembic upgrade head
```

Expected: `m_user` テーブルが `zaisan.db` に作成される

- [ ] **Step 12: Commit**

```bash
git add backend/models/ backend/tests/ backend/alembic.ini backend/alembic/ backend/requirements.txt
git commit -m "feat: add User model with Alembic migration setup"
```

---

## Task 3: JWT ブラックリスト + 監査ログモデル + マイグレーション

**Files:**
- Create: `backend/models/jwt_blacklist.py`
- Create: `backend/models/audit_log.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_models.py` に追記:
```python
from datetime import datetime
from models.jwt_blacklist import JWTBlacklist
from models.audit_log import AuditLog


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
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_models.py -v
```

Expected: FAIL（インポートエラー）

- [ ] **Step 3: `backend/models/jwt_blacklist.py` を作成**

```python
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class JWTBlacklist(Base):
    __tablename__ = "t_jwt_blacklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 4: `backend/models/audit_log.py` を作成**

```python
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class AuditLog(Base):
    __tablename__ = "t_audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    target_table: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    changed_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
```

- [ ] **Step 5: `alembic/env.py` にモデル import を追加**

```python
import models.jwt_blacklist  # noqa: F401
import models.audit_log  # noqa: F401
```

- [ ] **Step 6: マイグレーションを生成・適用**

```bash
cd backend
alembic revision --autogenerate -m "add jwt_blacklist and audit_log tables"
alembic upgrade head
```

- [ ] **Step 7: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_models.py -v
```

Expected: 7 passed

- [ ] **Step 8: 監査ログインデックスのマイグレーションを作成**

設計書 §5.6 に従い、インデックスを作成:

```bash
cd backend
alembic revision -m "add audit_log indexes"
```

生成されたファイルを編集:
```python
def upgrade() -> None:
    op.create_index("idx_audit_log_target", "t_audit_log", ["target_table", "target_id"])
    op.create_index("idx_audit_log_user", "t_audit_log", ["user_id"])
    op.create_index("idx_audit_log_time", "t_audit_log", ["performed_at"])
    op.create_index("idx_audit_log_target_time", "t_audit_log", ["target_table", "target_id", "performed_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_log_target_time")
    op.drop_index("idx_audit_log_time")
    op.drop_index("idx_audit_log_user")
    op.drop_index("idx_audit_log_target")
```

```bash
alembic upgrade head
```

- [ ] **Step 9: Commit**

```bash
git add backend/models/ backend/tests/test_models.py backend/alembic/
git commit -m "feat: add JWT blacklist and audit log models with indexes"
```

---

## Task 4: 認証サービス（パスワード + JWT）

**Files:**
- Create: `backend/auth.py`
- Create: `backend/tests/test_auth_service.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_auth_service.py`:
```python
import pytest
import time
from auth import (
    validate_password,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestValidatePassword:
    def test_valid_password(self):
        ok, msg = validate_password("Abc12345")
        assert ok is True
        assert msg == ""

    def test_too_short(self):
        ok, msg = validate_password("Ab12")
        assert ok is False
        assert "8文字" in msg

    def test_no_letters(self):
        ok, msg = validate_password("12345678")
        assert ok is False
        assert "英字" in msg

    def test_no_numbers(self):
        ok, msg = validate_password("Abcdefgh")
        assert ok is False
        assert "数字" in msg

    def test_minimum_valid(self):
        ok, msg = validate_password("A1b2c3d4")
        assert ok is True


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = hash_password("test1234Password")
        assert verify_password("test1234Password", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correctPassword1")
        assert verify_password("wrongPassword1", hashed) is False

    def test_different_hashes(self):
        h1 = hash_password("samePassword1")
        h2 = hash_password("samePassword1")
        assert h1 != h2  # bcrypt generates different salts


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token(user_id=1, username="tanaka", role="admin")
        payload = decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["username"] == "tanaka"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "jti" in payload

    def test_invalid_token(self):
        with pytest.raises(ValueError):
            decode_access_token("invalid.token.here")

    def test_token_has_jti(self):
        token = create_access_token(user_id=1, username="test", role="staff")
        payload = decode_access_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) > 0
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_auth_service.py -v
```

Expected: FAIL（`auth` モジュールが存在しない）

- [ ] **Step 3: `backend/auth.py` を作成**

```python
import re
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password(password: str) -> tuple[bool, str]:
    """パスワードポリシー検証: 8文字以上・英数字混在必須"""
    if len(password) < 8:
        return False, "パスワードは8文字以上で入力してください"
    if not re.search(r"[a-zA-Z]", password):
        return False, "英字を含めてください"
    if not re.search(r"[0-9]", password):
        return False, "数字を含めてください"
    return True, ""


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, username: str, role: str) -> str:
    jti = secrets.token_urlsafe(16)
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "jti": jti,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")
```

- [ ] **Step 4: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_auth_service.py -v
```

Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add backend/auth.py backend/tests/test_auth_service.py
git commit -m "feat: implement auth service with password hashing and JWT"
```

---

## Task 5: ログインエンドポイント

**Files:**
- Create: `backend/schemas/__init__.py`
- Create: `backend/schemas/auth.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/auth.py`
- Create: `backend/tests/test_auth_router.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_auth_router.py`:
```python
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

        # 4回失敗（ロックされない）
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_auth_router.py -v
```

Expected: FAIL

- [ ] **Step 3: `backend/schemas/__init__.py` を作成**

空ファイル。

- [ ] **Step 4: `backend/schemas/auth.py` を作成**

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    role: str

    model_config = {"from_attributes": True}


class LogoutRequest(BaseModel):
    token: str
```

- [ ] **Step 5: `backend/routers/__init__.py` を作成**

空ファイル。

- [ ] **Step 6: `backend/routers/auth.py` を作成**

```python
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, UserInfo
from auth import verify_password, create_access_token, decode_access_token
from models.jwt_blacklist import JWTBlacklist

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    """ログイン - JWTトークンを発行する"""
    user = db.query(User).filter(
        User.username == request.username,
        User.is_deleted == False,
    ).first()

    if not user or not verify_password(request.password, user.hashed_password):
        # 存在するユーザーの場合は失敗回数をインクリメント
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.is_locked = True
            db.commit()
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "ユーザー名またはパスワードが正しくありません"},
        )

    if user.is_locked:
        raise HTTPException(
            status_code=403,
            detail={"code": "ACCOUNT_LOCKED", "message": "アカウントがロックされています。管理者に連絡してください"},
        )

    # ログイン成功: 失敗回数リセット
    user.failed_login_count = 0
    db.commit()

    token = create_access_token(user.id, user.username, user.role)

    return {
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
            },
        },
        "message": "OK",
    }


@router.post("/logout")
def logout(request_body: dict, db: Session = Depends(get_db)):
    """ログアウト - JWTをブラックリストに追加する"""
    token = request_body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="token is required")

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    exp = payload.get("exp")

    blacklist_entry = JWTBlacklist(
        token_jti=jti,
        expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
    )
    db.add(blacklist_entry)
    db.commit()

    return {"data": None, "message": "ログアウトしました"}
```

- [ ] **Step 7: `backend/main.py` にルーターを登録**

```python
from routers.auth import router as auth_router

# ... 既存コード ...

app.include_router(auth_router)
```

- [ ] **Step 8: `conftest.py` に `client` フィクスチャを追加**

`conftest.py` に以下を追記:
```python
@pytest.fixture
def client(db_session):
    from main import app
    from database import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
```

- [ ] **Step 9: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_auth_router.py -v
```

Expected: 7 passed

- [ ] **Step 10: Commit**

```bash
git add backend/schemas/ backend/routers/ backend/tests/test_auth_router.py backend/main.py backend/tests/conftest.py
git commit -m "feat: add login endpoint with account lockout"
```

---

## Task 6: ログアウトエンドポイント + JWT ブラックリスト検証

**Files:**
- Modify: `backend/tests/test_auth_router.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_auth_router.py` に追記:
```python
class TestLogout:
    def test_logout_success(self, client, db_session):
        _create_test_user(db_session)

        # ログイン
        login_resp = client.post("/api/auth/login", json={
            "username": "tanaka",
            "password": "Password1",
        })
        token = login_resp.json()["data"]["access_token"]

        # ログアウト
        logout_resp = client.post("/api/auth/logout", json={"token": token})
        assert logout_resp.status_code == 200

    def test_logout_invalid_token(self, client):
        resp = client.post("/api/auth/logout", json={"token": "invalid"})
        assert resp.status_code == 401
```

- [ ] **Step 2: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_auth_router.py::TestLogout -v
```

Expected: 2 passed（Task 5 で既に実装済み）

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_auth_router.py
git commit -m "test: add logout endpoint tests"
```

---

## Task 7: 認証依存関係（Protected Routes + Role-Based Access）

**Files:**
- Modify: `backend/auth.py` (get_current_user, require_role を追加)
- Create: `backend/tests/test_auth_dependency.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_auth_dependency.py`:
```python
import pytest
from fastapi.testclient import TestClient
from models.user import User
from fastapi import Depends
from models.jwt_blacklist import JWTBlacklist
from auth import hash_password, create_access_token, decode_access_token
from datetime import datetime, timedelta, timezone


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
    def _setup_admin_route(self):
        """admin限定のテストエンドポイントを一時的に追加"""
        from main import app
        from auth import get_current_user, require_role

        @app.get("/api/admin-only")
        def admin_only(user=Depends(get_current_user)):
            from fastapi import HTTPException

            require_role(user, ["admin"])
            return {"data": {"message": "admin access"}}

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
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_auth_dependency.py -v
```

Expected: FAIL

- [ ] **Step 3: `backend/auth.py` に `get_current_user` と `require_role` を追加**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.jwt_blacklist import JWTBlacklist

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """JWTトークンから現在のユーザーを取得する"""
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "トークンが無効です"},
        )

    # ブラックリスト検査
    jti = payload.get("jti")
    blacklisted = db.query(JWTBlacklist).filter(
        JWTBlacklist.token_jti == jti
    ).first()
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_REVOKED", "message": "トークンは失効しています"},
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False,
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "ユーザーが見つかりません"},
        )

    return user


def require_role(user: User, allowed_roles: list[str]) -> None:
    """ユーザーのロールが許可リストに含まれているか検証する"""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "権限がありません"},
        )
```

- [ ] **Step 4: `/api/auth/me` エンドポイントを `routers/auth.py` に追加**

```python
from auth import get_current_user

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "role": current_user.role,
        },
        "message": "OK",
    }
```

- [ ] **Step 5: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_auth_dependency.py -v
```

Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add backend/auth.py backend/routers/auth.py backend/tests/test_auth_dependency.py
git commit -m "feat: add JWT authentication dependency with role-based access control"
```

---

## Task 8: 監査ログユーティリティ

**Files:**
- Create: `backend/audit.py`
- Create: `backend/tests/test_audit.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_audit.py`:
```python
import json
import pytest
from models.user import User
from models.audit_log import AuditLog
from auth import hash_password
from audit import log_audit


def _create_user(db_session):
    user = User(
        username="tanaka",
        hashed_password=hash_password("Password1"),
        display_name="田中太郎",
        role="staff",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestLogAudit:
    def test_log_create_action(self, db_session):
        user = _create_user(db_session)
        log_audit(
            db=db_session,
            user_id=user.id,
            action="CREATE",
            target_table="m_property",
            target_id=1,
            changed_fields=["property_code", "name"],
            before_value=None,
            after_value={"property_code": "P001", "name": "テスト財産"},
            ip_address="127.0.0.1",
        )

        logs = db_session.query(AuditLog).all()
        assert len(logs) == 1
        assert logs[0].action == "CREATE"
        assert logs[0].target_table == "m_property"
        assert logs[0].target_id == 1
        assert logs[0].user_id == user.id

    def test_log_with_before_after(self, db_session):
        user = _create_user(db_session)
        log_audit(
            db=db_session,
            user_id=user.id,
            action="UPDATE",
            target_table="m_property",
            target_id=1,
            changed_fields=["name"],
            before_value={"name": "旧名称"},
            after_value={"name": "新名称"},
        )

        log = db_session.query(AuditLog).first()
        assert json.loads(log.before_value) == {"name": "旧名称"}
        assert json.loads(log.after_value) == {"name": "新名称"}
        assert json.loads(log.changed_fields) == ["name"]

    def test_log_login_action(self, db_session):
        user = _create_user(db_session)
        log_audit(
            db=db_session,
            user_id=user.id,
            action="LOGIN",
            target_table="m_user",
            target_id=user.id,
            ip_address="192.168.1.1",
        )

        log = db_session.query(AuditLog).first()
        assert log.action == "LOGIN"
        assert log.ip_address == "192.168.1.1"
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_audit.py -v
```

Expected: FAIL

- [ ] **Step 3: `backend/audit.py` を作成**

```python
import json
from typing import Any
from sqlalchemy.orm import Session
from models.audit_log import AuditLog


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    target_table: str,
    target_id: int | None = None,
    changed_fields: list[str] | None = None,
    before_value: Any = None,
    after_value: Any = None,
    ip_address: str | None = None,
) -> AuditLog:
    """監査ログを記録する。

    Args:
        db: DBセッション
        user_id: 操作ユーザーID
        action: 操作種別 (CREATE/UPDATE/DELETE/LOGIN/EXPORT/PDF_GEN)
        target_table: 操作対象テーブル名
        target_id: 操作対象レコードID
        changed_fields: 変更フィールド一覧
        before_value: 変更前の値（dictの場合はJSON文字列化）
        after_value: 変更後の値（dictの場合はJSON文字列化）
        ip_address: クライアントIPアドレス
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_table=target_table,
        target_id=target_id,
        changed_fields=json.dumps(changed_fields) if changed_fields else None,
        before_value=json.dumps(before_value, ensure_ascii=False) if before_value is not None else None,
        after_value=json.dumps(after_value, ensure_ascii=False) if after_value is not None else None,
        ip_address=ip_address,
    )
    db.add(log)
    db.flush()  # commit は呼び出し元で行う
    return log
```

- [ ] **Step 4: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_audit.py -v
```

Expected: 3 passed

- [ ] **Step 5: ログイン時に監査ログを記録するように `routers/auth.py` を修正**

`login` 関数の成功時（`user.failed_login_count = 0` の後）に:
```python
from audit import log_audit

# ... 既存の成功処理 ...
log_audit(
    db=db,
    user_id=user.id,
    action="LOGIN",
    target_table="m_user",
    target_id=user.id,
    ip_address=req.client.host if req.client else None,
)
```

- [ ] **Step 6: Commit**

```bash
git add backend/audit.py backend/tests/test_audit.py backend/routers/auth.py
git commit -m "feat: add audit logging utility and integrate with login"
```

---

## Task 9: ステータス遷移マシン

**Files:**
- Create: `backend/services/__init__.py`
- Create: `backend/services/status_machine.py`
- Create: `backend/tests/test_status_machine.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_status_machine.py`:
```python
import pytest
from services.status_machine import is_valid_transition, get_allowed_transitions


class TestPermissionTransitions:
    def test_draft_to_submitted(self):
        assert is_valid_transition("permission", "draft", "submitted") is True

    def test_submitted_to_under_review(self):
        assert is_valid_transition("permission", "submitted", "under_review") is True

    def test_under_review_to_pending_approval(self):
        assert is_valid_transition("permission", "under_review", "pending_approval") is True

    def test_pending_approval_to_approved(self):
        assert is_valid_transition("permission", "pending_approval", "approved") is True

    def test_approved_to_issued(self):
        assert is_valid_transition("permission", "approved", "issued") is True

    def test_approved_to_expired(self):
        assert is_valid_transition("permission", "approved", "expired") is True

    def test_approved_to_cancelled(self):
        assert is_valid_transition("permission", "approved", "cancelled") is True

    def test_under_review_to_rejected(self):
        assert is_valid_transition("permission", "under_review", "rejected") is True

    def test_pending_approval_to_rejected(self):
        assert is_valid_transition("permission", "pending_approval", "rejected") is True

    def test_rejected_to_submitted(self):
        """差戻し後の再申請"""
        assert is_valid_transition("permission", "rejected", "submitted") is True

    def test_invalid_draft_to_approved(self):
        assert is_valid_transition("permission", "draft", "approved") is False

    def test_invalid_approved_to_submitted(self):
        """逆戻り禁止"""
        assert is_valid_transition("permission", "approved", "submitted") is False

    def test_invalid_expired_to_approved(self):
        """expired は終端状態"""
        assert is_valid_transition("permission", "expired", "approved") is False

    def test_invalid_cancelled_to_draft(self):
        """cancelled は終端状態"""
        assert is_valid_transition("permission", "cancelled", "draft") is False


class TestLeaseTransitions:
    def test_draft_to_negotiating(self):
        assert is_valid_transition("lease", "draft", "negotiating") is True

    def test_negotiating_to_pending_approval(self):
        assert is_valid_transition("lease", "negotiating", "pending_approval") is True

    def test_pending_approval_to_active(self):
        assert is_valid_transition("lease", "pending_approval", "active") is True

    def test_pending_approval_to_negotiating(self):
        """差戻し"""
        assert is_valid_transition("lease", "pending_approval", "negotiating") is True

    def test_active_to_expired(self):
        assert is_valid_transition("lease", "active", "expired") is True

    def test_active_to_terminated(self):
        assert is_valid_transition("lease", "active", "terminated") is True

    def test_invalid_draft_to_active(self):
        assert is_valid_transition("lease", "draft", "active") is False

    def test_invalid_active_to_draft(self):
        assert is_valid_transition("lease", "active", "draft") is False

    def test_invalid_terminated_to_active(self):
        """terminated は終端状態"""
        assert is_valid_transition("lease", "terminated", "active") is False


class TestGetAllowedTransitions:
    def test_permission_draft_allowed(self):
        allowed = get_allowed_transitions("permission", "draft")
        assert "submitted" in allowed
        assert "approved" not in allowed

    def test_permission_approved_allowed(self):
        allowed = get_allowed_transitions("permission", "approved")
        assert "issued" in allowed
        assert "expired" in allowed
        assert "cancelled" in allowed
        assert "submitted" not in allowed

    def test_lease_active_allowed(self):
        allowed = get_allowed_transitions("lease", "active")
        assert "expired" in allowed
        assert "terminated" in allowed
        assert "draft" not in allowed

    def test_unknown_status(self):
        allowed = get_allowed_transitions("permission", "unknown_status")
        assert allowed == []

    def test_unknown_case_type(self):
        allowed = get_allowed_transitions("unknown_type", "draft")
        assert allowed == []
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_status_machine.py -v
```

Expected: FAIL

- [ ] **Step 3: `backend/services/__init__.py` を作成**

空ファイル。

- [ ] **Step 4: `backend/services/status_machine.py` を作成**

```python
from enum import Enum


class PermissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ISSUED = "issued"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class LeaseStatus(str, Enum):
    DRAFT = "draft"
    NEGOTIATING = "negotiating"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


# 設計書 §2.4.2, §2.4.4 に基づく遷移ルール
PERMISSION_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["submitted"],
    "submitted": ["under_review"],
    "under_review": ["rejected", "pending_approval"],
    "pending_approval": ["rejected", "approved"],
    "approved": ["issued", "expired", "cancelled"],
    "issued": ["expired", "cancelled"],
    "rejected": ["submitted"],
    # expired, cancelled は終端状態（更新は新レコードで表現）
}

LEASE_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["negotiating"],
    "negotiating": ["pending_approval"],
    "pending_approval": ["negotiating", "active"],
    "active": ["expired", "terminated"],
    # expired, terminated は終端状態（更新は新レコードで表現）
}


def is_valid_transition(case_type: str, current_status: str, new_status: str) -> bool:
    """ステータス遷移が許可されているか検証する。

    Args:
        case_type: "permission" または "lease"
        current_status: 現在のステータス
        new_status: 遷移先ステータス

    Returns:
        遷移が許可されていれば True
    """
    transitions = (
        PERMISSION_TRANSITIONS if case_type == "permission"
        else LEASE_TRANSITIONS if case_type == "lease"
        else {}
    )
    allowed = transitions.get(current_status, [])
    return new_status in allowed


def get_allowed_transitions(case_type: str, current_status: str) -> list[str]:
    """現在のステータスから遷移可能なステータス一覧を取得する。

    フロントエンドのボタン表示制御に使用する。
    """
    transitions = (
        PERMISSION_TRANSITIONS if case_type == "permission"
        else LEASE_TRANSITIONS if case_type == "lease"
        else {}
    )
    return transitions.get(current_status, [])
```

- [ ] **Step 5: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_status_machine.py -v
```

Expected: 29 passed

- [ ] **Step 6: Commit**

```bash
git add backend/services/ backend/tests/test_status_machine.py
git commit -m "feat: implement status transition machine for permission and lease"
```

---

## Task 10: 共通エラーレスポンスハンドラ

**Files:**
- Create: `backend/schemas/common.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_error_handler.py`

- [ ] **Step 1: 失敗するテストを書く**

`backend/tests/test_error_handler.py`:
```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認**

```bash
cd backend
pytest tests/test_error_handler.py -v
```

Expected: FAIL（404のレスポンス形式がデフォルトのため）

- [ ] **Step 3: `backend/schemas/common.py` を作成**

```python
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    total_pages: int
```

- [ ] **Step 4: `backend/main.py` にエラーハンドラを追加**

```python
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "リソースが見つかりません",
                "detail": {"path": str(request.url)},
            }
        },
    )


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "UNAUTHORIZED",
                "message": "認証が必要です",
            }
        },
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "FORBIDDEN",
                "message": "権限がありません",
            }
        },
    )


# 422 (Pydantic バリデーションエラー) のフォーマット
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "入力内容に誤りがあります",
                "detail": {"errors": errors},
            }
        },
    )
```

- [ ] **Step 5: テストを実行して成功を確認**

```bash
cd backend
pytest tests/test_error_handler.py -v
```

Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add backend/schemas/common.py backend/main.py backend/tests/test_error_handler.py
git commit -m "feat: add unified error response handlers"
```

---

## Task 11: 全テスト実行 + 統合確認

**Files:** なし（既存テストの実行のみ）

- [ ] **Step 1: 全テストを実行**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: 全テスト PASS（約50テスト以上）

- [ ] **Step 2: Swagger UI でエンドポイントを確認**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

ブラウザで `http://localhost:8000/docs` を開き、以下を確認:
- `/api/auth/login` - POST
- `/api/auth/logout` - POST
- `/api/auth/me` - GET（鍵マーク付き）
- `/api/health` - GET

- [ ] **Step 3: Swagger UI から手動テスト**

1. `/api/auth/login` でログイン（seed データがない場合は Task 12 で作成）
2. 返ってきた `access_token` を Authorize ボタンに入力
3. `/api/auth/me` でユーザー情報を取得できることを確認

---

## Task 12: 初期データシードスクリプト

**Files:**
- Create: `backend/seed.py`

- [ ] **Step 1: `backend/seed.py` を作成**

```python
"""初期データ作成スクリプト - 管理者アカウントとテストユーザーを作成する

Usage:
    cd backend
    python seed.py
"""

from database import SessionLocal, engine, Base
from models.user import User
from auth import hash_password


def seed():
    # テーブルが存在しない場合は作成
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 既存データ確認
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("管理者アカウントは既に存在します: admin")
            return

        # 管理者アカウント
        admin = User(
            username="admin",
            hashed_password=hash_password("Admin123"),
            display_name="システム管理者",
            role="admin",
            department="財政課",
        )
        db.add(admin)

        # 一般職員
        staff1 = User(
            username="tanaka",
            hashed_password=hash_password("Tanaka123"),
            display_name="田中太郎",
            role="staff",
            department="財産管理担当",
        )
        db.add(staff1)

        # 閲覧専用
        viewer = User(
            username="sato",
            hashed_password=hash_password("Sato12345"),
            display_name="佐藤花子",
            role="viewer",
            department="監査室",
        )
        db.add(viewer)

        db.commit()
        print("初期データを作成しました:")
        print("  管理者: admin / Admin123")
        print("  職員: tanaka / Tanaka123")
        print("  閲覧: sato / Sato12345")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: シードを実行**

```bash
cd backend
source venv/bin/activate
python seed.py
```

Expected:
```
初期データを作成しました:
  管理者: admin / Admin123
  職員: tanaka / Tanaka123
  閲覧: sato / Sato12345
```

- [ ] **Step 3: curl でログイン確認**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123"}'
```

Expected: `access_token` を含む JSON レスポンス

- [ ] **Step 4: `/api/auth/me` で認証確認**

```bash
TOKEN=<上記で取得したaccess_token>
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
```

Expected: 管理者ユーザー情報

- [ ] **Step 5: Commit**

```bash
git add backend/seed.py
git commit -m "feat: add seed script for initial admin and test user accounts"
```

---

## Task 13: Frontend プロジェクト構築

**Files:**
- Create: `frontend/` (Vite + React プロジェクト全体)

- [ ] **Step 1: Vite + React プロジェクトを作成**

```bash
cd /home/hart/p-system
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom
```

- [ ] **Step 2: `frontend/vite.config.js` を修正（API プロキシ）**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: `frontend/src/api/client.js` を作成**

```javascript
/**
 * API クライアント - JWT認証付き fetch ラッパー
 */

function getToken() {
  return sessionStorage.getItem('access_token')
}

function setToken(token) {
  sessionStorage.setItem('access_token', token)
}

function clearToken() {
  sessionStorage.removeItem('access_token')
}

async function apiClient(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(path, { ...options, headers })

  if (response.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('認証エラー')
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody?.error?.message || `API Error: ${response.status}`)
  }

  return response.json()
}

export { apiClient, setToken, clearToken, getToken }
```

- [ ] **Step 4: `frontend/src/api/auth.js` を作成**

```javascript
import { apiClient, setToken, clearToken } from './client'

export async function login(username, password) {
  const data = await apiClient('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  setToken(data.data.access_token)
  return data.data.user
}

export async function logout() {
  const token = sessionStorage.getItem('access_token')
  if (token) {
    await apiClient('/api/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }).catch(() => {})
  }
  clearToken()
}

export async function getMe() {
  const data = await apiClient('/api/auth/me')
  return data.data
}
```

- [ ] **Step 5: `frontend/src/contexts/AuthContext.jsx` を作成**

```jsx
import { createContext, useContext, useState, useEffect } from 'react'
import { getMe } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = sessionStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => {
        sessionStorage.removeItem('access_token')
      })
      .finally(() => setLoading(false))
  }, [])

  const value = { user, setUser, loading }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

- [ ] **Step 6: `frontend/src/components/ProtectedRoute.jsx` を作成**

```jsx
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div>読み込み中...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <div>権限がありません</div>
  }

  return children
}
```

- [ ] **Step 7: `frontend/src/pages/Login.jsx` を作成**

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { setUser } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const user = await login(username, password)
      setUser(user)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '100px auto', padding: '0 20px' }}>
      <h1>自治体財産管理システム</h1>
      <h2>ログイン</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">ユーザー名</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
          />
        </div>
        <div>
          <label htmlFor="password">パスワード</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'ログイン中...' : 'ログイン'}
        </button>
      </form>
    </div>
  )
}
```

- [ ] **Step 8: `frontend/src/pages/DashboardPlaceholder.jsx` を作成**

```jsx
import { useAuth } from '../contexts/AuthContext'
import { logout } from '../api/auth'
import { useNavigate } from 'react-router-dom'

export default function DashboardPlaceholder() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    setUser(null)
    navigate('/login')
  }

  return (
    <div>
      <header>
        <h1>自治体財産管理システム</h1>
        <div>
          <span>{user?.display_name} ({user?.role})</span>
          <button onClick={handleLogout}>ログアウト</button>
        </div>
      </header>
      <main>
        <h2>ダッシュボード（開発中）</h2>
        <p>認証・共通基盤の動作確認用ページです。</p>
        <p>Plan 2 以降でダッシュボードを実装します。</p>
      </main>
    </div>
  )
}
```

- [ ] **Step 9: `frontend/src/App.jsx` を修正**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Login from './pages/Login'
import DashboardPlaceholder from './pages/DashboardPlaceholder'
import ProtectedRoute from './components/ProtectedRoute'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPlaceholder />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
```

- [ ] **Step 10: `frontend/src/App.css` を最小化**

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #333;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #1a365d;
  color: white;
}

header h1 {
  font-size: 18px;
}

form div {
  margin-bottom: 12px;
}

label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

button {
  padding: 8px 16px;
  background: #2b6cb0;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:hover {
  background: #2c5282;
}

button:disabled {
  background: #a0aec0;
  cursor: not-allowed;
}

main {
  padding: 24px;
}
```

- [ ] **Step 11: フロントエンド起動確認**

```bash
# ターミナル1: バックエンド
cd backend
source venv/bin/activate
python seed.py  # 初期データが未作成の場合
uvicorn main:app --reload --port 8000

# ターミナル2: フロントエンド
cd frontend
npm run dev
```

ブラウザで `http://localhost:3000` を開く → `/login` にリダイレクトされる

- [ ] **Step 12: E2E動作確認**

1. ユーザー名 `admin`、パスワード `Admin123` でログイン
2. `/dashboard` にリダイレクトされることを確認
3. ヘッダーに「システム管理者 (admin)」が表示されることを確認
4. 「ログアウト」ボタンで `/login` に戻ることを確認
5. 権限エラーの確認: `sato` (viewer) でログインし、admin限定ページ（将来実装）にアクセスできないことを確認

- [ ] **Step 13: Commit**

```bash
git add frontend/
git commit -m "feat: add React frontend with login page and auth context"
```

---

## Task 14: 最終確認 + クリーンアップ

**Files:** 既存ファイルの確認

- [ ] **Step 1: 全バックエンドテストを実行**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: 全テスト PASS

- [ ] **Step 2: テストカバレッジを確認（任意）**

```bash
cd backend
pip install pytest-cov
pytest tests/ --cov=. --cov-report=term-missing --tb=short
```

- [ ] **Step 3: 不要なファイルを確認・削除**

```bash
# テストDBが残っていたら削除
rm -f backend/test_zaisan.db
```

- [ ] **Step 4: 最終 Commit**

```bash
git add -A
git status  # 確認
git commit -m "chore: cleanup and final verification for auth-common-infrastructure plan"
```

---

## 完了条件

Plan 1 完了時、以下が動作する状態になる:

- [x] `http://localhost:8000/docs` で Swagger UI が表示される
- [x] `POST /api/auth/login` で JWT トークンが取得できる
- [x] `GET /api/auth/me` で認証済みユーザー情報が取得できる
- [x] 5回連続ログイン失敗でアカウントがロックされる
- [x] ログアウトで JWT がブラックリストに追加される
- [x] ロールベースのアクセス制御が動作する
- [x] 監査ログが記録される
- [x] ステータス遷移ルールが検証できる
- [x] `http://localhost:3000` でログイン画面が表示される
- [x] ログイン後ダッシュボード（仮）に遷移する
