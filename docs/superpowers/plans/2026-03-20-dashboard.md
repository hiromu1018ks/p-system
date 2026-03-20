# Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dashboard placeholder with a fully functional dashboard showing KPI cards, status chart, expiry alerts, and recent audit logs.

**Architecture:** Single backend endpoint `GET /api/dashboard/summary` returns all dashboard data in one response. Frontend composes the Dashboard page from 3 child components (StatusChart, ExpiryAlerts, RecentLogs) plus inline KPI cards.

**Tech Stack:** FastAPI + SQLAlchemy (backend), React 19 + Recharts (frontend)

**Spec:** `docs/superpowers/specs/2026-03-20-dashboard-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `backend/routers/dashboard.py` | Single `GET /api/dashboard/summary` endpoint with all aggregation queries |
| `backend/tests/test_dashboard_router.py` | Tests for the dashboard API |
| `frontend/src/api/dashboard.js` | API client function for the dashboard endpoint |
| `frontend/src/pages/Dashboard.jsx` | Main dashboard page — KPI cards, FY total, quick links, assembles child components |
| `frontend/src/components/StatusChart.jsx` | Recharts grouped bar chart for status distribution |
| `frontend/src/components/ExpiryAlerts.jsx` | Colour-coded expiry alert list |
| `frontend/src/components/RecentLogs.jsx` | Audit log table with action badges |
| `frontend/src/App.jsx` | Update import from DashboardPlaceholder to Dashboard |

---

### Task 1: Dashboard API Tests (TDD — write tests first)

**Files:**
- Create: `backend/tests/test_dashboard_router.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_dashboard_router.py
from datetime import date, timedelta
import pytest


class TestDashboardSummary:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/dashboard/summary")
        assert resp.status_code == 401

    def test_empty_dashboard(self, auth_client):
        resp = auth_client.get("/api/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["active_permissions"] == 0
        assert data["active_leases"] == 0
        assert data["expiring_soon"] == 0
        assert data["new_this_month"] == 0
        assert data["fy_total"] == 0
        assert data["status_distribution"]["permissions"] == []
        assert data["status_distribution"]["leases"] == []
        assert data["expiry_alerts"] == []
        assert data["recent_logs"] == []

    def test_active_permission_count(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="テスト公園", property_code="P0001", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        for status in ["draft", "submitted", "under_review", "pending_approval", "approved", "issued"]:
            p = Permission(
                property_id=prop.id, applicant_name=f"申請者{status}",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status,
            )
            db_session.add(p)
        # Terminal statuses should NOT count
        for status in ["expired", "cancelled", "rejected"]:
            p = Permission(
                property_id=prop.id, applicant_name=f"終了{status}",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status,
            )
            db_session.add(p)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_permissions"] == 6

    def test_active_lease_count(self, auth_client, db_session):
        from models.property import Property
        from models.lease import Lease

        prop = Property(name="テスト土地", property_code="P0002", property_type="general")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        for status in ["draft", "negotiating", "pending_approval", "active"]:
            l = Lease(
                property_id=prop.id, lessee_name=f"借受人{status}",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status, property_sub_type="land",
            )
            db_session.add(l)
        for status in ["expired", "terminated"]:
            l = Lease(
                property_id=prop.id, lessee_name=f"終了{status}",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status, property_sub_type="land",
            )
            db_session.add(l)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_leases"] == 4

    def test_deleted_cases_excluded(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="削除テスト", property_code="P0010", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        # Active case
        p1 = Permission(
            property_id=prop.id, applicant_name="有効",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved",
        )
        # Deleted case (should NOT count)
        p2 = Permission(
            property_id=prop.id, applicant_name="削除済み",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved", is_deleted=True,
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_permissions"] == 1

    def test_is_latest_case_false_excluded(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="最新テスト", property_code="P0011", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        # Old renewal (is_latest_case=False)
        p1 = Permission(
            property_id=prop.id, applicant_name="旧案件",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved", is_latest_case=False,
        )
        # Latest renewal (is_latest_case=True)
        p2 = Permission(
            property_id=prop.id, applicant_name="新案件",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="draft", is_latest_case=True,
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_permissions"] == 1

    def test_new_this_month(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="月次テスト", property_code="P0006", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        # This month
        p1 = Permission(
            property_id=prop.id, applicant_name="今月案件",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved",
        )
        # Last month (created_at will be set by DB, so we just add another one this month)
        p2 = Permission(
            property_id=prop.id, applicant_name="今月案件2",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="draft",
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        # Both were created "now" which is this month
        assert resp.json()["data"]["new_this_month"] >= 2

    def test_fy_total(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="年度テスト", property_code="P0007", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        p = Permission(
            property_id=prop.id, applicant_name="今年度案件",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved",
        )
        db_session.add(p)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        # Created now, which is within current FY
        assert resp.json()["data"]["fy_total"] >= 1

    def test_expiry_alerts_permissions(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="アラート公園", property_code="P0003", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        today = date.today()
        # Expiring in 5 days
        p1 = Permission(
            property_id=prop.id, applicant_name="急ぎ案件",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=5),
            status="approved",
        )
        # Expiring in 60 days (should NOT appear)
        p2 = Permission(
            property_id=prop.id, applicant_name="遠い未来",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=60),
            status="approved",
        )
        # Already expired (should NOT appear)
        p3 = Permission(
            property_id=prop.id, applicant_name="期限切れ",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today - timedelta(days=1),
            status="approved",
        )
        # Rejected case (should NOT appear)
        p4 = Permission(
            property_id=prop.id, applicant_name="差戻し案件",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=3),
            status="rejected",
        )
        db_session.add_all([p1, p2, p3, p4])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        alerts = resp.json()["data"]["expiry_alerts"]
        assert len(alerts) == 1
        assert alerts[0]["days_remaining"] == 5
        assert alerts[0]["applicant_name"] == "急ぎ案件"
        assert alerts[0]["property_name"] == "アラート公園"

    def test_expiry_alerts_leases(self, auth_client, db_session):
        from models.property import Property
        from models.lease import Lease

        prop = Property(name="アラート土地", property_code="P0008", property_type="general")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        today = date.today()
        l1 = Lease(
            property_id=prop.id, lessee_name="借受人急ぎ",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=10),
            status="active", property_sub_type="land",
        )
        db_session.add(l1)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        alerts = resp.json()["data"]["expiry_alerts"]
        lease_alerts = [a for a in alerts if a["case_type"] == "lease"]
        assert len(lease_alerts) == 1
        assert lease_alerts[0]["days_remaining"] == 10
        assert lease_alerts[0]["property_name"] == "アラート土地"

    def test_expiry_alerts_sorted_by_urgency(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="ソートテスト", property_code="P0009", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        today = date.today()
        p1 = Permission(
            property_id=prop.id, applicant_name="10日後",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=10),
            status="approved",
        )
        p2 = Permission(
            property_id=prop.id, applicant_name="3日後",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=3),
            status="approved",
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        alerts = resp.json()["data"]["expiry_alerts"]
        assert alerts[0]["days_remaining"] < alerts[1]["days_remaining"]

    def test_recent_logs(self, auth_client, db_session):
        from models.audit_log import AuditLog

        log = AuditLog(
            user_id=auth_client.user.id,
            action="CREATE",
            target_table="t_permission",
            target_id=99,
        )
        db_session.add(log)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        logs = resp.json()["data"]["recent_logs"]
        assert len(logs) == 1
        assert logs[0]["action"] == "CREATE"
        assert logs[0]["user_name"] == "田中太郎"

    def test_fiscal_year_label(self, auth_client):
        resp = auth_client.get("/api/dashboard/summary")
        data = resp.json()["data"]
        today = date.today()
        fy = today.year if today.month >= 4 else today.year - 1
        assert data["fy_label"] == f"R{fy % 100}年度"

    def test_status_distribution(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="分布テスト", property_code="P0005", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        for _ in range(3):
            p = Permission(
                property_id=prop.id, applicant_name="テスト",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status="approved",
            )
            db_session.add(p)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        dist = resp.json()["data"]["status_distribution"]["permissions"]
        approved = [d for d in dist if d["status"] == "approved"]
        assert len(approved) == 1
        assert approved[0]["count"] == 3
```

- [ ] **Step 2: Run tests to verify they fail (no router yet)**

Run: `cd backend && python -m pytest tests/test_dashboard_router.py -v`
Expected: FAIL (404 or import error — router not yet registered)

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_dashboard_router.py
git commit -m "test: add dashboard API tests (TDD)"
```

---

### Task 2: Dashboard API Endpoint

**Files:**
- Create: `backend/routers/dashboard.py`
- Modify: `backend/main.py` (register router)

- [ ] **Step 1: Create the dashboard router**

```python
# backend/routers/dashboard.py
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.user import User
from models.permission import Permission
from models.lease import Lease
from models.property import Property
from models.audit_log import AuditLog

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

PERMISSION_ACTIVE_STATUSES = ("draft", "submitted", "under_review", "pending_approval", "approved", "issued")
LEASE_ACTIVE_STATUSES = ("draft", "negotiating", "pending_approval", "active")
PERMISSION_EXPIRY_EXCLUDE = ("expired", "cancelled", "rejected")
LEASE_EXPIRY_EXCLUDE = ("expired", "terminated")


def _fiscal_year(today: date) -> tuple[int, str]:
    """Return (fy_start_year, display_label) for Japanese fiscal year."""
    fy = today.year if today.month >= 4 else today.year - 1
    return fy, f"R{fy % 100}年度"


def _status_distribution(db: Session) -> dict:
    """Count cases by status for permissions and leases."""
    perm_rows = (
        db.query(Permission.status, func.count(Permission.id))
        .filter(Permission.is_deleted == False, Permission.is_latest_case == True)
        .group_by(Permission.status)
        .all()
    )
    lease_rows = (
        db.query(Lease.status, func.count(Lease.id))
        .filter(Lease.is_deleted == False, Lease.is_latest_case == True)
        .group_by(Lease.status)
        .all()
    )
    return {
        "permissions": [{"status": r[0], "count": r[1]} for r in perm_rows],
        "leases": [{"status": r[0], "count": r[1]} for r in lease_rows],
    }


def _expiry_alerts(db: Session, today: date) -> list[dict]:
    """Find cases expiring within 30 days. Selects property name via join (no N+1)."""
    deadline = today + timedelta(days=30)

    perm_alerts = (
        db.query(
            Permission.id,
            Permission.permission_number,
            Permission.applicant_name,
            Permission.end_date,
            Property.name.label("property_name"),
        )
        .join(Property, Permission.property_id == Property.id)
        .filter(
            Permission.is_deleted == False,
            Permission.is_latest_case == True,
            Permission.end_date > today,
            Permission.end_date <= deadline,
        )
        .filter(~Permission.status.in_(PERMISSION_EXPIRY_EXCLUDE))
        .all()
    )
    lease_alerts = (
        db.query(
            Lease.id,
            Lease.lease_number,
            Lease.lessee_name,
            Lease.end_date,
            Property.name.label("property_name"),
        )
        .join(Property, Lease.property_id == Property.id)
        .filter(
            Lease.is_deleted == False,
            Lease.is_latest_case == True,
            Lease.end_date > today,
            Lease.end_date <= deadline,
        )
        .filter(~Lease.status.in_(LEASE_EXPIRY_EXCLUDE))
        .all()
    )

    alerts = []
    for row in perm_alerts:
        alerts.append({
            "case_type": "permission",
            "case_id": row.id,
            "case_number": row.permission_number or "-",
            "applicant_name": row.applicant_name,
            "property_name": row.property_name or "-",
            "end_date": row.end_date.isoformat(),
            "days_remaining": (row.end_date - today).days,
        })
    for row in lease_alerts:
        alerts.append({
            "case_type": "lease",
            "case_id": row.id,
            "case_number": row.lease_number or "-",
            "applicant_name": row.lessee_name,
            "property_name": row.property_name or "-",
            "end_date": row.end_date.isoformat(),
            "days_remaining": (row.end_date - today).days,
        })

    alerts.sort(key=lambda x: x["days_remaining"])
    return alerts


def _recent_logs(db: Session) -> list[dict]:
    """Get 10 most recent audit log entries. Batch-lookup summaries to avoid N+1."""
    logs = (
        db.query(AuditLog, User.display_name)
        .outerjoin(User, AuditLog.user_id == User.id)
        .order_by(AuditLog.performed_at.desc())
        .limit(10)
        .all()
    )

    if not logs:
        return []

    # Collect target IDs per table for batch lookup
    perm_ids = set()
    lease_ids = set()
    prop_ids = set()
    for log, _ in logs:
        if log.target_table == "t_permission" and log.target_id:
            perm_ids.add(log.target_id)
        elif log.target_table == "t_lease" and log.target_id:
            lease_ids.add(log.target_id)
        elif log.target_table == "m_property" and log.target_id:
            prop_ids.add(log.target_id)

    # Batch fetch summaries
    perm_map = {}
    if perm_ids:
        rows = db.query(Permission.id, Permission.permission_number).filter(Permission.id.in_(perm_ids)).all()
        perm_map = {r[0]: r[1] for r in rows}

    lease_map = {}
    if lease_ids:
        rows = db.query(Lease.id, Lease.lease_number).filter(Lease.id.in_(lease_ids)).all()
        lease_map = {r[0]: r[1] for r in rows}

    prop_map = {}
    if prop_ids:
        rows = db.query(Property.id, Property.property_code).filter(Property.id.in_(prop_ids)).all()
        prop_map = {r[0]: r[1] for r in rows}

    result = []
    for log, user_name in logs:
        summary = ""
        if log.target_table == "t_permission" and log.target_id in perm_map:
            num = perm_map[log.target_id]
            if num:
                summary = f"使用許可 {num}"
        elif log.target_table == "t_lease" and log.target_id in lease_map:
            num = lease_map[log.target_id]
            if num:
                summary = f"普通財産貸付 {num}"
        elif log.target_table == "m_property" and log.target_id in prop_map:
            code = prop_map[log.target_id]
            if code:
                summary = f"財産 {code}"

        result.append({
            "performed_at": log.performed_at.isoformat() if log.performed_at else None,
            "user_name": user_name or "-",
            "action": log.action,
            "target_table": log.target_table,
            "target_id": log.target_id,
            "summary": summary,
        })
    return result


@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    fy_year, fy_label = _fiscal_year(today)
    fy_start = date(fy_year, 4, 1)
    month_start = date(today.year, today.month, 1)
    deadline = today + timedelta(days=30)

    active_permissions = (
        db.query(func.count(Permission.id))
        .filter(Permission.is_deleted == False, Permission.is_latest_case == True)
        .filter(Permission.status.in_(PERMISSION_ACTIVE_STATUSES))
        .scalar() or 0
    )
    active_leases = (
        db.query(func.count(Lease.id))
        .filter(Lease.is_deleted == False, Lease.is_latest_case == True)
        .filter(Lease.status.in_(LEASE_ACTIVE_STATUSES))
        .scalar() or 0
    )

    expiring_count = (
        db.query(func.count(Permission.id))
        .filter(
            Permission.is_deleted == False, Permission.is_latest_case == True,
            Permission.end_date > today, Permission.end_date <= deadline,
        )
        .filter(~Permission.status.in_(PERMISSION_EXPIRY_EXCLUDE))
        .scalar() or 0
    ) + (
        db.query(func.count(Lease.id))
        .filter(
            Lease.is_deleted == False, Lease.is_latest_case == True,
            Lease.end_date > today, Lease.end_date <= deadline,
        )
        .filter(~Lease.status.in_(LEASE_EXPIRY_EXCLUDE))
        .scalar() or 0
    )

    new_this_month = (
        db.query(func.count(Permission.id))
        .filter(
            Permission.is_deleted == False, Permission.is_latest_case == True,
            func.date(Permission.created_at) >= month_start,
        )
        .scalar() or 0
    ) + (
        db.query(func.count(Lease.id))
        .filter(
            Lease.is_deleted == False, Lease.is_latest_case == True,
            func.date(Lease.created_at) >= month_start,
        )
        .scalar() or 0
    )

    fy_total = (
        db.query(func.count(Permission.id))
        .filter(
            Permission.is_deleted == False, Permission.is_latest_case == True,
            func.date(Permission.created_at) >= fy_start,
        )
        .scalar() or 0
    ) + (
        db.query(func.count(Lease.id))
        .filter(
            Lease.is_deleted == False, Lease.is_latest_case == True,
            func.date(Lease.created_at) >= fy_start,
        )
        .scalar() or 0
    )

    return {
        "data": {
            "active_permissions": active_permissions,
            "active_leases": active_leases,
            "expiring_soon": expiring_count,
            "new_this_month": new_this_month,
            "fy_total": fy_total,
            "fy_label": fy_label,
            "status_distribution": _status_distribution(db),
            "expiry_alerts": _expiry_alerts(db, today),
            "recent_logs": _recent_logs(db),
        },
        "message": "OK",
    }
```

- [ ] **Step 2: Register the router in main.py**

In `backend/main.py`, add the import and include:

```python
# Add to imports (after line 15):
from routers.dashboard import router as dashboard_router

# Add after app.include_router(pdf_router) (after line 57):
app.include_router(dashboard_router)
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_dashboard_router.py -v`
Expected: All 13 tests PASS

- [ ] **Step 4: Commit**

```bash
git add backend/routers/dashboard.py backend/main.py
git commit -m "feat: add dashboard summary API endpoint"
```

---

### Task 3: Install Recharts and Create API Client

**Files:**
- Modify: `frontend/package.json` (add recharts dependency)
- Create: `frontend/src/api/dashboard.js`

- [ ] **Step 1: Install recharts**

Run: `cd frontend && npm install recharts`
Expected: recharts added to package.json dependencies

- [ ] **Step 2: Create the dashboard API client**

```javascript
// frontend/src/api/dashboard.js
import { apiClient } from './client'

export async function getDashboardSummary() {
  const response = await apiClient('/api/dashboard/summary')
  return response.data
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/api/dashboard.js
git commit -m "feat: add recharts dependency and dashboard API client"
```

---

### Task 4: StatusChart Component

**Files:**
- Create: `frontend/src/components/StatusChart.jsx`

- [ ] **Step 1: Create the StatusChart component**

```jsx
// frontend/src/components/StatusChart.jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const STATUS_LABELS = {
  draft: '下書き',
  submitted: '申請受付済み',
  under_review: '審査中',
  pending_approval: '決裁待ち',
  approved: '決裁完了',
  issued: '交付済み',
  negotiating: '協議中',
  active: '契約中',
  rejected: '差戻し',
  expired: '期間終了',
  cancelled: '取消',
  terminated: '解約',
}

export default function StatusChart({ statusDistribution }) {
  const { permissions, leases } = statusDistribution

  const allStatuses = new Set([
    ...permissions.map(p => p.status),
    ...leases.map(l => l.status),
  ])

  const data = [...allStatuses].map(status => ({
    name: STATUS_LABELS[status] || status,
    使用許可: permissions.find(p => p.status === status)?.count || 0,
    普通財産貸付: leases.find(l => l.status === status)?.count || 0,
  }))

  if (data.length === 0) {
    return <p style={{ color: '#a0aec0', textAlign: 'center', padding: 20 }}>データなし</p>
  }

  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>ステータス別件数</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="使用許可" fill="#90cdf4" radius={[2, 2, 0, 0]} />
          <Bar dataKey="普通財産貸付" fill="#3182ce" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/StatusChart.jsx
git commit -m "feat: add StatusChart component with Recharts"
```

---

### Task 5: ExpiryAlerts Component

**Files:**
- Create: `frontend/src/components/ExpiryAlerts.jsx`

- [ ] **Step 1: Create the ExpiryAlerts component**

```jsx
// frontend/src/components/ExpiryAlerts.jsx
import { useNavigate } from 'react-router-dom'

function getUrgencyStyle(days) {
  if (days <= 7) return { bg: '#fff5f5', border: '#e53e3e', text: '#e53e3e' }
  if (days <= 15) return { bg: '#fffaf0', border: '#ed8936', text: '#ed8936' }
  return { bg: '#fffff0', border: '#d69e2e', text: '#d69e2e' }
}

export default function ExpiryAlerts({ alerts }) {
  const navigate = useNavigate()

  if (alerts.length === 0) {
    return (
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>有効期限アラート</div>
        <p style={{ color: '#38a169', textAlign: 'center', padding: 12, margin: 0 }}>期限切れ間近の案件はありません</p>
      </div>
    )
  }

  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#e53e3e', marginBottom: 12 }}>有効期限アラート</div>
      <div>
        {alerts.map(alert => {
          const style = getUrgencyStyle(alert.days_remaining)
          const route = alert.case_type === 'permission' ? `/permissions/${alert.case_id}` : `/leases/${alert.case_id}`
          return (
            <div
              key={`${alert.case_type}-${alert.case_id}`}
              onClick={() => navigate(route)}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: 8, background: style.bg, borderRadius: 4,
                marginBottom: 6, borderLeft: `3px solid ${style.border}`, cursor: 'pointer',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{alert.case_number} / {alert.applicant_name}</div>
                <div style={{ fontSize: 11, color: '#718096' }}>{alert.property_name}</div>
              </div>
              <div style={{ color: style.text, fontWeight: 700, fontSize: 13, whiteSpace: 'nowrap' }}>
                あと{alert.days_remaining}日
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ExpiryAlerts.jsx
git commit -m "feat: add ExpiryAlerts component"
```

---

### Task 6: RecentLogs Component

**Files:**
- Create: `frontend/src/components/RecentLogs.jsx`

- [ ] **Step 1: Create the RecentLogs component**

```jsx
// frontend/src/components/RecentLogs.jsx
const BADGE_STYLES = {
  CREATE: { bg: '#c6f6d5', color: '#276749' },
  UPDATE: { bg: '#dbeafe', color: '#1e40af' },
  DELETE: { bg: '#fed7d7', color: '#9b2c2c' },
  PDF_GEN: { bg: '#e9d8fd', color: '#6b46c1' },
  LOGIN: { bg: '#e2e8f0', color: '#4a5568' },
  EXPORT: { bg: '#e2e8f0', color: '#4a5568' },
}

function ActionBadge({ action }) {
  const style = BADGE_STYLES[action] || { bg: '#e2e8f0', color: '#4a5568' }
  return (
    <span style={{
      background: style.bg, color: style.color,
      padding: '2px 6px', borderRadius: 3, fontSize: 10, fontWeight: 600,
    }}>
      {action}
    </span>
  )
}

function formatDateTime(isoString) {
  if (!isoString) return '-'
  const d = new Date(isoString)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}/${dd} ${hh}:${mi}`
}

export default function RecentLogs({ logs }) {
  if (logs.length === 0) {
    return (
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>最近の操作履歴</div>
        <p style={{ color: '#a0aec0', textAlign: 'center', padding: 12, margin: 0 }}>データなし</p>
      </div>
    )
  }

  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>最近の操作履歴</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>日時</th>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>操作者</th>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>操作</th>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>対象</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
              <td style={{ padding: '6px 8px' }}>{formatDateTime(log.performed_at)}</td>
              <td style={{ padding: '6px 8px' }}>{log.user_name}</td>
              <td style={{ padding: '6px 8px' }}><ActionBadge action={log.action} /></td>
              <td style={{ padding: '6px 8px' }}>{log.summary || `${log.target_table} #${log.target_id}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/RecentLogs.jsx
git commit -m "feat: add RecentLogs component"
```

---

### Task 7: Dashboard Page

**Files:**
- Create: `frontend/src/pages/Dashboard.jsx`

- [ ] **Step 1: Create the Dashboard page**

```jsx
// frontend/src/pages/Dashboard.jsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { logout } from '../api/auth'
import { getDashboardSummary } from '../api/dashboard'
import StatusChart from '../components/StatusChart'
import ExpiryAlerts from '../components/ExpiryAlerts'
import RecentLogs from '../components/RecentLogs'

function KpiCard({ label, value, color, subtext }) {
  return (
    <div style={{
      background: 'white', border: color ? `1px solid ${color}33` : '1px solid #e2e8f0',
      borderLeft: color ? `3px solid ${color}` : 'none',
      borderRadius: 6, padding: 16, textAlign: 'center',
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#2b6cb0' }}>{value}</div>
      <div style={{ fontSize: 12, color: '#718096', marginTop: 4 }}>{label}</div>
      {subtext && <div style={{ fontSize: 10, color: '#a0aec0', marginTop: 2 }}>{subtext}</div>}
    </div>
  )
}

function QuickLink({ label, sublabel, to }) {
  const navigate = useNavigate()
  return (
    <div
      onClick={() => navigate(to)}
      style={{
        flex: 1, background: '#2b6cb0', color: 'white', borderRadius: 6,
        padding: 16, textAlign: 'center', cursor: 'pointer',
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 10, opacity: 0.8, marginTop: 2 }}>{sublabel}</div>
    </div>
  )
}

export default function Dashboard() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboardSummary()
      .then(setData)
      .catch(err => alert(err.message))
      .finally(() => setLoading(false))
  }, [])

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
        {/* KPI Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
          <KpiCard
            label="使用許可案件中"
            value={loading ? '...' : (data?.active_permissions ?? 0)}
            color="#2b6cb0"
            subtext="(有効案件のみ)"
          />
          <KpiCard
            label="貸付案件中"
            value={loading ? '...' : (data?.active_leases ?? 0)}
            color="#2b6cb0"
            subtext="(有効案件のみ)"
          />
          <KpiCard
            label="期限切れ間近"
            value={loading ? '...' : (data?.expiring_soon ?? 0)}
            color="#e53e3e"
            subtext="(30日以内)"
          />
          <KpiCard
            label="今月新規"
            value={loading ? '...' : (data?.new_this_month ?? 0)}
            color="#38a169"
            subtext="(許可+貸付)"
          />
        </div>

        {/* FY Total + Quick Links */}
        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 12, marginBottom: 20 }}>
          <div style={{
            background: 'white', border: '1px solid #e2e8f0', borderRadius: 6,
            padding: 16, textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          }}>
            <div style={{ fontSize: 12, color: '#718096', marginBottom: 4 }}>
              {loading ? '...' : data?.fy_label}累計
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#2d3748' }}>
              {loading ? '...' : (data?.fy_total ?? 0)}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <QuickLink label="財産台帳" sublabel="管理画面へ" to="/properties" />
            <QuickLink label="使用許可" sublabel="案件一覧へ" to="/permissions" />
            <QuickLink label="普通財産貸付" sublabel="案件一覧へ" to="/leases" />
          </div>
        </div>

        {/* Chart + Alerts */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          {loading ? (
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, textAlign: 'center' }}>
              <p>読み込み中...</p>
            </div>
          ) : data ? (
            <>
              <StatusChart statusDistribution={data.status_distribution} />
              <ExpiryAlerts alerts={data.expiry_alerts} />
            </>
          ) : null}
        </div>

        {/* Recent Logs */}
        {loading ? (
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, textAlign: 'center' }}>
            <p>読み込み中...</p>
          </div>
        ) : data ? (
          <RecentLogs logs={data.recent_logs} />
        ) : null}
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx
git commit -m "feat: add Dashboard page with KPI cards and layout"
```

---

### Task 8: Wire Up Dashboard in App.jsx

**Files:**
- Modify: `frontend/src/App.jsx`
- Delete: `frontend/src/pages/DashboardPlaceholder.jsx`

- [ ] **Step 1: Update App.jsx imports and route**

In `frontend/src/App.jsx`:

1. Replace line 4:
```jsx
// Old:
import DashboardPlaceholder from './pages/DashboardPlaceholder'
// New:
import Dashboard from './pages/Dashboard'
```

2. Replace line 27 (inside the ProtectedRoute for `/dashboard`):
```jsx
// Old:
<DashboardPlaceholder />
// New:
<Dashboard />
```

- [ ] **Step 2: Delete the placeholder file**

Run: `rm frontend/src/pages/DashboardPlaceholder.jsx`

- [ ] **Step 3: Verify the app builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

- [ ] **Step 4: Run backend tests**

Run: `cd backend && python -m pytest tests/test_dashboard_router.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.jsx frontend/src/pages/DashboardPlaceholder.jsx
git commit -m "feat: replace DashboardPlaceholder with Dashboard, wire up routing"
```
