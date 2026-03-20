# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

自治体財産管理システム — a Japanese local government property management system for administrative property usage permissions (行政財産使用許可) and general property leases (普通財産貸付). All UI text is in Japanese.

## Development Commands

### Backend (run from `backend/`)
```bash
# Setup
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
alembic upgrade head
python seed.py

# Dev server (port 8000)
uvicorn main:app --reload

# Tests (uses SQLite test_zaisan.db)
pytest                           # all tests
pytest tests/test_auth_router.py # single file
pytest -k "test_login"           # single test by name

# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend (run from `frontend/`)
```bash
npm install
npm run dev      # Vite dev server on port 3000 (proxies /api to :8000)
npm run build    # production build
npm run lint     # ESLint
```

## Architecture

### Structure
```
backend/   # Python FastAPI + SQLAlchemy + SQLite (WAL mode)
frontend/  # React 19 + Vite 8, plain JSX (no TypeScript), plain CSS (no Tailwind)
docs/      # Design documents
```

### Backend: 3-Layer Architecture
- **Routers** (`routers/`) — HTTP endpoints, request/response mapping
- **Services** (`services/`) — Business logic, state transitions, fee calculation, PDF generation
- **Models** (`models/`) — SQLAlchemy ORM, table naming: `m_` (master), `t_` (transactional)

### API Response Format
All responses use an envelope: `{"data": ..., "message": "OK"}` for success, `{"error": {"code": "...", "message": "...", "detail": {...}}}` for errors.

### Key Domain Patterns
- **Status machine** (`services/status_machine.py`) — All status transitions must go through explicit allowed-transition maps. Never change status directly.
- **Optimistic locking** — Status changes require `expected_current_status` + `expected_updated_at` from the client.
- **Logical deletion** — `is_deleted` flag everywhere; never hard-delete.
- **Change history** — `_history` tables store JSON snapshots on every CRUD operation.
- **Audit logging** — `log_audit()` tracks user, action, table, before/after values, IP on all mutations.
- **Renewals** — Create new records linked via `parent_case_id`, not updates.
- **Auto-numbering** — Property codes `P0001`; permission numbers `R{FY}-使-{seq}`; lease numbers `R{FY}-貸-{seq}` (Japanese fiscal year, April start).
- **Fee calculation** (`services/fee_calculator.py`) — 7-step formula using `Decimal`; amounts are integers (yen).
- **PDF generation** — WeasyPrint + Jinja2 templates (`templates/`) + IPAex Japanese fonts (`fonts/`).

### Frontend Patterns
- **Routing** — React Router DOM v7, all routes except `/login` wrapped in `<ProtectedRoute>`
- **Auth** — JWT in `sessionStorage`, `AuthContext` for React state, `apiClient()` auto-injects Bearer token and redirects on 401
- **Styling** — Global `App.css` + inline styles; no component library
- **API layer** (`api/`) — One module per domain (auth, properties, permissions, leases, fees, files, pdf, dashboard)

### Authentication
JWT-based with 3 roles: `admin`, `staff`, `viewer`. Token blacklist for logout.

### Seed Users
- admin / Admin123 (admin, 財政課)
- tanaka / Tanaka123 (staff, 財産管理担当)
- sato / Sato12345 (viewer, 監査室)

## Constraints
- No TypeScript — frontend is plain `.jsx`
- No Tailwind or CSS framework
- No state management library beyond React Context
- SQLite only (no PostgreSQL/MySQL planned)
- No Docker or CI/CD configured
