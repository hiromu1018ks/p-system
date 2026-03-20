# Missing Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all features from the design document (`docs/design-document.md`) that are not yet built.

**Architecture:** Backend uses 3-layer architecture (routers/services/models). Frontend uses React 19 + plain JSX + plain CSS. All new features follow existing patterns.

**Tech Stack:** Python/FastAPI, SQLAlchemy, React 19, Vite 8, Recharts

---

## Gap Analysis Summary

| No | Feature | Backend | Frontend | Status |
|----|---------|---------|----------|--------|
| F-01 | 財産台帳管理 | ✅ | ✅ | **DONE** |
| F-02 | 地図連携 | ✅ | ✅ | **DONE** |
| F-03 | 添付ファイル管理 | ✅ | ⚠️ No upload UI | **PARTIAL** |
| F-04 | 使用許可申請管理 | ✅ | ✅ | **DONE** |
| F-05 | 普通財産貸付管理 | ✅ | ✅ | **DONE** |
| F-06 | 使用料・賃料自動計算 | ✅ | ✅ | **DONE** |
| F-07 | 使用許可証PDF | ✅ | ✅ | **DONE** |
| F-08 | 土地貸付契約書PDF | ✅ | ✅ | **DONE** |
| F-09 | 建物貸付契約書PDF | ✅ | ✅ | **DONE** |
| F-10 | 更新通知文PDF | ✅ | ✅ | **DONE** |
| F-11 | 有効期限アラート | ✅ | ✅ | **DONE** |
| F-12 | 案件検索・一覧 | ✅ | ✅ | **DONE** |
| F-13 | ダッシュボード | ✅ | ✅ | **DONE** |
| F-14 | 変更履歴表示 | ✅ | ✅ | **DONE** |
| F-15 | CSVエクスポート | ❌ | ❌ | **MISSING** |
| F-16 | 一括賃料改定 | ❌ | ❌ | **MISSING** |
| SCR-12 | マスタ管理 | ❌ | ❌ | **MISSING** |
| SCR-13 | 一括賃料改定画面 | ❌ | ❌ | **MISSING** |

### Bugs to Fix

| Bug | Location | Description |
|-----|----------|-------------|
| User role from wrong source | `PermissionDetail.jsx`, `LeaseDetail.jsx` | Reads role from `sessionStorage.getItem('user')` which is never set. Should use `useAuth().user.role` |
| Role-based routes not enforced | `App.jsx` | `ProtectedRoute` accepts `allowedRoles` but no route uses it |

---

## Task 1: Fix User Role Bug

**Files:**
- Modify: `frontend/src/pages/PermissionDetail.jsx`
- Modify: `frontend/src/pages/LeaseDetail.jsx`

- [ ] **Step 1: Fix PermissionDetail.jsx**

Replace `sessionStorage` role reading with `useAuth()` hook. Add `useAuth` import and replace:

```jsx
// Before (broken):
const user = JSON.parse(sessionStorage.getItem('user') || '{}');
const userRole = user.role || 'staff';

// After (fixed):
import { useAuth } from '../contexts/AuthContext';
// ... inside component:
const { user } = useAuth();
const userRole = user?.role || 'staff';
```

- [ ] **Step 2: Fix LeaseDetail.jsx**

Same fix as Step 1.

- [ ] **Step 3: Verify**

Run `npm run dev` in frontend, navigate to a permission detail and lease detail page as admin user, confirm status transition buttons show correctly.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/PermissionDetail.jsx frontend/src/pages/LeaseDetail.jsx
git commit -m "fix: use AuthContext for user role instead of sessionStorage"
```

---

## Task 2: Add File Upload UI

**Files:**
- Create: `frontend/src/components/FileUploader.jsx`
- Modify: `frontend/src/components/FileList.jsx`
- Modify: `frontend/src/pages/PropertyDetail.jsx`
- Modify: `frontend/src/pages/PermissionDetail.jsx`
- Modify: `frontend/src/pages/LeaseDetail.jsx`

- [ ] **Step 1: Create FileUploader component**

```jsx
// frontend/src/components/FileUploader.jsx
import { useState } from 'react';
import { uploadFile } from '../api/files';

export default function FileUploader({ relatedType, relatedId, fileType, onUploaded }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      await uploadFile(relatedType, relatedId, fileType || 'other', file);
      e.target.value = '';
      if (onUploaded) onUploaded();
    } catch (err) {
      setError(err.message || 'アップロードに失敗しました');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ marginTop: 12 }}>
      <label style={{
        display: 'inline-block',
        padding: '6px 16px',
        background: '#2b6cb0',
        color: '#fff',
        borderRadius: 4,
        cursor: uploading ? 'not-allowed' : 'pointer',
        opacity: uploading ? 0.6 : 1,
      }}>
        {uploading ? 'アップロード中...' : 'ファイルを追加'}
        <input
          type="file"
          style={{ display: 'none' }}
          onChange={handleUpload}
          disabled={uploading}
        />
      </label>
      {error && <p style={{ color: '#e53e3e', fontSize: 13, marginTop: 4 }}>{error}</p>}
    </div>
  );
}
```

- [ ] **Step 2: Integrate FileUploader into FileList**

Add `FileUploader` as an optional prop to `FileList` so it appears at the top of the file list. In `FileList.jsx`, import `FileUploader` and render it when `showUpload` prop is true:

```jsx
// At the top of the file list rendering:
{showUpload && (
  <FileUploader
    relatedType={relatedType}
    relatedId={relatedId}
    onUploaded={fetchFiles}
  />
)}
```

Update `FileList` props to accept `showUpload` (default false).

- [ ] **Step 3: Enable upload in detail pages**

In `PropertyDetail.jsx`, `PermissionDetail.jsx`, and `LeaseDetail.jsx`, pass `showUpload={true}` to `FileList` in the files tab.

- [ ] **Step 4: Verify**

Upload a file to a property, permission, and lease. Confirm it appears in the list and can be downloaded.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/FileUploader.jsx frontend/src/components/FileList.jsx frontend/src/pages/PropertyDetail.jsx frontend/src/pages/PermissionDetail.jsx frontend/src/pages/LeaseDetail.jsx
git commit -m "feat: add file upload UI to detail pages"
```

---

## Task 3: CSV Export (F-15)

### 3A: Backend

**Files:**
- Create: `backend/routers/export.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_export_router.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_export_router.py
import pytest

def test_export_permissions_unauthenticated(client):
    resp = client.get("/api/export/permissions")
    assert resp.status_code == 401

def test_export_permissions_success(auth_client, db_session):
    from models.property import Property
    from models.permission import Permission
    from datetime import date
    prop = Property(property_code="P0001", name="Test", property_type="administrative")
    db_session.add(prop)
    db_session.commit()
    perm = Permission(
        property_id=prop.id, applicant_name="Test User",
        start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
    )
    db_session.add(perm)
    db_session.commit()

    resp = auth_client.get("/api/export/permissions")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.content
    # UTF-8 BOM check
    assert body[:3] == b'\xef\xbb\xbf'
    # Contains Japanese headers
    assert "許可番号".encode("utf-8") in body

def test_export_leases_success(auth_client, db_session):
    from models.property import Property
    from models.lease import Lease
    from datetime import date
    prop = Property(property_code="P0001", name="Test", property_type="general")
    db_session.add(prop)
    db_session.commit()
    lease = Lease(
        property_id=prop.id, property_sub_type="land", lessee_name="Test Corp",
        start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
    )
    db_session.add(lease)
    db_session.commit()

    resp = auth_client.get("/api/export/leases")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.content
    assert body[:3] == b'\xef\xbb\xbf'
    assert "契約番号".encode("utf-8") in body
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_export_router.py -v`
Expected: FAIL (module not found / 404)

- [ ] **Step 3: Implement export router**

> **Note:** CSV export returns `StreamingResponse` instead of the standard JSON envelope format. This is a justified deviation since file downloads cannot use the JSON envelope pattern.

```python
# backend/routers/export.py
import csv
import io
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from audit import log_audit
from models.property import Property
from models.permission import Permission
from models.lease import Lease
from models.user import User

router = APIRouter(prefix="/api/export", tags=["export"])

def _csv_response(filename, rows, headers):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    csv_bytes = output.getvalue().encode("utf-8-sig")  # UTF-8 BOM (design doc §3.6)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/permissions")
def export_permissions(
    status: str = Query(None),
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Permission, Property).outerjoin(
        Property, Permission.property_id == Property.id
    ).filter(Permission.is_deleted == False)
    if status:
        query = query.filter(Permission.status == status)
    results = query.all()

    log_audit(db, user.id, "EXPORT", "t_permission", None,
              changed_fields=["status_filter"], before_value=None,
              after_value={"status": status, "count": len(results)},
              ip_address=request.client.host)

    headers = ["許可番号", "財産名称", "申請者氏名", "申請者住所", "使用目的",
               "使用開始日", "使用終了日", "使用面積(㎡)", "使用料(円)",
               "ステータス", "許可年月日"]
    rows = []
    for perm, prop in results:
        rows.append([
            perm.permission_number or "",
            prop.name if prop else "",
            perm.applicant_name,
            perm.applicant_address or "",
            perm.purpose or "",
            perm.start_date.isoformat() if perm.start_date else "",
            perm.end_date.isoformat() if perm.end_date else "",
            str(perm.usage_area_sqm) if perm.usage_area_sqm else "",
            str(perm.fee_amount) if perm.fee_amount else "",
            perm.status,
            perm.permission_date.isoformat() if perm.permission_date else "",
        ])
    return _csv_response("permissions.csv", rows, headers)

@router.get("/leases")
def export_leases(
    status: str = Query(None),
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Lease, Property).outerjoin(
        Property, Lease.property_id == Property.id
    ).filter(Lease.is_deleted == False)
    if status:
        query = query.filter(Lease.status == status)
    results = query.all()

    log_audit(db, user.id, "EXPORT", "t_lease", None,
              changed_fields=["status_filter"], before_value=None,
              after_value={"status": status, "count": len(results)},
              ip_address=request.client.host)

    headers = ["契約番号", "財産名称", "財産種別", "借受者氏名", "借受者住所",
               "貸付目的", "契約開始日", "契約終了日", "貸付面積・部屋番号",
               "年間賃料(円)", "支払方法", "ステータス"]
    rows = []
    for lease, prop in results:
        rows.append([
            lease.lease_number or "",
            prop.name if prop else "",
            "土地" if lease.property_sub_type == "land" else "建物",
            lease.lessee_name,
            lease.lessee_address or "",
            lease.purpose or "",
            lease.start_date.isoformat() if lease.start_date else "",
            lease.end_date.isoformat() if lease.end_date else "",
            lease.leased_area or "",
            str(lease.annual_rent) if lease.annual_rent else "",
            lease.payment_method or "",
            lease.status,
        ])
    return _csv_response("leases.csv", rows, headers)
```

Register router in `main.py`:
```python
from routers import export
app.include_router(export.router)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_export_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routers/export.py backend/main.py backend/tests/test_export_router.py
git commit -m "feat: add CSV export API for permissions and leases"
```

### 3B: Frontend

**Files:**
- Modify: `frontend/src/api/permissions.js`
- Modify: `frontend/src/api/leases.js`
- Modify: `frontend/src/pages/PermissionList.jsx`
- Modify: `frontend/src/pages/LeaseList.jsx`

- [ ] **Step 1: Add export API functions**

Use `getToken` from `client.js` (not inline `sessionStorage` access) since CSV responses are not JSON and `apiClient()` parses JSON:

In `frontend/src/api/permissions.js`:
```js
import { getToken } from './client';

export async function exportPermissions(status) {
  const params = status ? `?status=${status}` : '';
  const token = getToken();
  const res = await fetch(`/api/export/permissions${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('エクスポートに失敗しました');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '使用許可案件.csv';
  a.click();
  URL.revokeObjectURL(url);
}
```

In `frontend/src/api/leases.js`:
```js
import { getToken } from './client';

export async function exportLeases(status) {
  const params = status ? `?status=${status}` : '';
  const token = getToken();
  const res = await fetch(`/api/export/leases${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('エクスポートに失敗しました');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '貸付案件.csv';
  a.click();
  URL.revokeObjectURL(url);
}
```

- [ ] **Step 2: Add export button to PermissionList**

Add a "CSVエクスポート" button at the top of the list page, next to search/filter controls.

- [ ] **Step 3: Add export button to LeaseList**

Same as Step 2.

- [ ] **Step 4: Verify**

Click export button on both list pages. Confirm CSV downloads with correct Japanese headers and UTF-8 BOM.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/permissions.js frontend/src/api/leases.js frontend/src/pages/PermissionList.jsx frontend/src/pages/LeaseList.jsx
git commit -m "feat: add CSV export button to permission and lease list pages"
```

---

## Task 4: Master Admin Page (SCR-12)

### 4A: User Management Backend

**Files:**
- Modify: `backend/routers/auth.py`
- Modify: `backend/schemas/auth.py`
- Create: `backend/tests/test_user_management.py`

- [ ] **Step 1: Add UserCreateSchema to schemas/auth.py**

```python
# backend/schemas/auth.py — add:
class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(admin|staff|viewer)$")
    department: str | None = Field(None, max_length=100)
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_user_management.py
def test_list_users_admin_only(admin_client, auth_client):
    resp = admin_client.get("/api/auth/users")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1

    resp = auth_client.get("/api/auth/users")
    assert resp.status_code == 403

def test_list_users_viewer_denied(viewer_client):
    """Viewer role should be denied access to user management."""
    resp = viewer_client.get("/api/auth/users")
    assert resp.status_code == 403

def test_unlock_user(admin_client, auth_client, db_session):
    from models.user import User
    user = db_session.query(User).filter_by(username="tanaka").first()
    user.is_locked = True
    db_session.commit()

    resp = admin_client.post(f"/api/auth/users/{user.id}/unlock")
    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.is_locked == False
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
        "username": "admin",  # already exists
        "password": "NewUser123",
        "display_name": "Dup",
        "role": "staff",
    })
    assert resp.status_code == 400

def test_create_user_invalid_password(admin_client):
    resp = admin_client.post("/api/auth/users", json={
        "username": "badpass",
        "password": "short",  # too short, no numbers
        "display_name": "Bad",
        "role": "staff",
    })
    assert resp.status_code == 422
```

Note: `viewer_client` fixture may need to be added to `conftest.py` if it doesn't exist. Check existing fixtures and add if needed.

- [ ] **Step 3: Implement user management endpoints in auth router**

Add to `backend/routers/auth.py`. Reuse existing `validate_password()` from `auth.py` (line ~19) and `hash_password()`:

```python
from auth import get_current_user, require_role, validate_password, hash_password
from schemas.auth import UserCreateSchema
from audit import log_audit

@router.get("/users")
def list_users(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(user, ["admin"])
    users = db.query(User).filter(User.is_deleted == False).all()
    log_audit(db, user.id, "READ", "m_user", None,
              changed_fields=None, before_value=None, after_value=None,
              ip_address=request.client.host)
    return {"data": [{"id": u.id, "username": u.username, "display_name": u.display_name,
                      "role": u.role, "department": u.department, "is_locked": u.is_locked,
                      "created_at": u.created_at.isoformat() if u.created_at else None}
                     for u in users], "message": "OK"}

@router.post("/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(user, ["admin"])
    target = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not target:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    before = {"is_locked": target.is_locked, "failed_login_count": target.failed_login_count}
    target.is_locked = False
    target.failed_login_count = 0
    db.commit()
    log_audit(db, user.id, "UPDATE", "m_user", target.id,
              changed_fields=["is_locked", "failed_login_count"],
              before_value=before,
              after_value={"is_locked": False, "failed_login_count": 0},
              ip_address=request.client.host)
    return {"data": None, "message": "OK"}

@router.post("/users", status_code=201)
def create_user(
    body: UserCreateSchema,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(user, ["admin"])
    # Validate password using existing utility
    validate_password(body.password)
    # Check username uniqueness
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="ユーザー名は既に使用されています")
    new_user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role=body.role,
        department=body.department,
    )
    db.add(new_user)
    db.flush()
    log_audit(db, user.id, "CREATE", "m_user", new_user.id,
              changed_fields=["username", "display_name", "role", "department"],
              before_value=None,
              after_value={"username": body.username, "role": body.role},
              ip_address=request.client.host)
    db.commit()
    return {"data": {"id": new_user.id, "username": new_user.username,
                     "display_name": new_user.display_name, "role": new_user.role},
            "message": "OK"}
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_user_management.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routers/auth.py backend/schemas/auth.py backend/tests/test_user_management.py
git commit -m "feat: add user management API (list, create, unlock)"
```

### 4B: Master Admin Frontend (Unit Prices + User Management)

**Files:**
- Create: `frontend/src/pages/MasterAdmin.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/Layout.jsx`
- Modify: `frontend/src/App.css`
- Modify: `frontend/src/api/auth.js`

- [ ] **Step 1: Add frontend API functions for user management**

In `frontend/src/api/auth.js`:
```js
export function getUsers() { return apiClient('/api/auth/users'); }
export function createUser(data) { return apiClient('/api/auth/users', { method: 'POST', body: JSON.stringify(data) }); }
export function unlockUser(userId) { return apiClient(`/api/auth/users/${userId}/unlock`, { method: 'POST' }); }
```

- [ ] **Step 2: Create MasterAdmin page**

The page has two tabs: "単価マスタ" (Unit Prices), "ユーザー管理" (User Management).

**Unit Price tab:**
- Table: property_type, usage, unit_price, start_date, end_date
- "新規登録" button → form (property_type dropdown, usage text, unit_price number, start_date)
- Uses existing `getUnitPrices()`, `createUnitPrice()`, `updateUnitPrice()` from `api/fees.js`

**User Management tab:**
- Table: username, display_name, role, department, is_locked, created_at
- "新規ユーザー登録" button → form (username, password, display_name, role dropdown, department)
- "ロック解除" button for locked users
- Uses `getUsers()`, `createUser()`, `unlockUser()` from `api/auth.js`

**Admin-only guard** at top of component:
```jsx
import { useAuth } from '../contexts/AuthContext';

export default function MasterAdmin() {
  const { user } = useAuth();
  if (user?.role !== 'admin') {
    return <p>管理者のみアクセス可能です。</p>;
  }
  // ... tabbed interface
}
```

- [ ] **Step 3: Add route and nav link**

In `App.jsx`:
```jsx
<Route path="/master-admin" element={<MasterAdmin />} />
```

In `Layout.jsx`: Add "マスタ管理" nav link, conditionally rendered only when `user.role === 'admin'`. Import `useAuth` in Layout.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/MasterAdmin.jsx frontend/src/App.jsx frontend/src/components/Layout.jsx frontend/src/App.css frontend/src/api/auth.js
git commit -m "feat: add master admin page with unit price and user management"
```

---

## Task 5: Bulk Fee Update (F-16, SCR-13)

### 5A: Backend

**Files:**
- Modify: `backend/routers/leases.py` (endpoint lives here since path is `/api/leases/bulk-update-fee`)
- Modify: `backend/schemas/fee.py`
- Create: `backend/tests/test_bulk_fee.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_bulk_fee.py
import pytest
from datetime import date

def _create_active_lease(db_session, property_type="general", sub_type="land"):
    from models.property import Property
    from models.lease import Lease
    prop = Property(property_code="P_BULK", name="Bulk Test", property_type=property_type)
    db_session.add(prop)
    db_session.flush()
    lease = Lease(
        property_id=prop.id, property_sub_type=sub_type,
        lessee_name="Bulk Corp", start_date=date(2024, 4, 1), end_date=date(2025, 3, 31),
        status="active"
    )
    db_session.add(lease)
    db_session.flush()
    return lease

def test_bulk_fee_update_unauthenticated(client):
    resp = client.post("/api/leases/bulk-update-fee", json={})
    assert resp.status_code == 401

def test_bulk_fee_update_staff_denied(auth_client):
    resp = auth_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": [1], "new_unit_price": 500
    })
    assert resp.status_code == 403

def test_bulk_fee_update_success(admin_client, db_session):
    lease1 = _create_active_lease(db_session)
    lease2 = _create_active_lease(db_session)
    db_session.commit()

    resp = admin_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": [lease1.id, lease2.id],
        "new_unit_price": 500,
        "discount_rate": 0.0,
        "tax_rate": 0.10,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["updated_count"] == 2

    # Verify fee_details were created
    from models.fee_detail import FeeDetail
    for lid in [lease1.id, lease2.id]:
        fees = db_session.query(FeeDetail).filter(
            FeeDetail.case_id == lid, FeeDetail.case_type == "lease", FeeDetail.is_latest == True
        ).all()
        assert len(fees) == 1
        assert fees[0].unit_price == 500

    # Verify lease annual_rent was updated
    db_session.refresh(lease1)
    assert lease1.annual_rent is not None and lease1.annual_rent > 0

def test_bulk_fee_update_max_100(admin_client):
    ids = list(range(1, 102))
    resp = admin_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": ids, "new_unit_price": 500
    })
    assert resp.status_code == 400

def test_bulk_fee_update_non_active_fails(admin_client, db_session):
    from models.property import Property
    from models.lease import Lease
    prop = Property(property_code="P_DRAFT", name="Draft", property_type="general")
    db_session.add(prop)
    db_session.flush()
    lease = Lease(
        property_id=prop.id, property_sub_type="land",
        lessee_name="Draft Corp", start_date=date(2024, 4, 1), end_date=date(2025, 3, 31),
        status="draft"
    )
    db_session.add(lease)
    db_session.commit()

    resp = admin_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": [lease.id], "new_unit_price": 500
    })
    assert resp.status_code == 400

def test_bulk_fee_preview(admin_client, db_session):
    """Preview endpoint returns calculations without persisting."""
    lease = _create_active_lease(db_session)
    db_session.commit()

    resp = admin_client.post("/api/leases/bulk-preview", json={
        "lease_ids": [lease.id],
        "new_unit_price": 500,
        "discount_rate": 0.0,
        "tax_rate": 0.10,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 1
    assert data["items"][0]["lease_id"] == lease.id
    assert data["items"][0]["new_total_amount"] > 0

    # Verify nothing was persisted
    from models.fee_detail import FeeDetail
    count = db_session.query(FeeDetail).filter(FeeDetail.case_id == lease.id).count()
    assert count == 0
```

- [ ] **Step 2: Add BulkFeeUpdateRequest schema**

Add to `backend/schemas/fee.py`:
```python
class BulkFeeUpdateRequest(BaseModel):
    lease_ids: list[int] = Field(..., min_length=1, max_length=100)
    new_unit_price: int = Field(..., gt=0)
    discount_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    tax_rate: float = Field(default=0.10, ge=0.0, le=1.0)
    discount_reason: str | None = None
```

- [ ] **Step 3: Implement bulk fee update and preview endpoints**

Add to `backend/routers/leases.py` (endpoint path is `/api/leases/bulk-update-fee` per design doc §6.4):

```python
from fastapi import Request
from audit import log_audit
from schemas.fee import BulkFeeUpdateRequest
from models.fee_detail import FeeDetail
from models.property import Property
from services.fee_calculator import calculate_fee

@router.post("/bulk-preview")
def bulk_fee_preview(
    body: BulkFeeUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dry-run preview: calculate new fees without persisting."""
    require_role(user, ["admin"])

    leases = db.query(Lease).filter(
        Lease.id.in_(body.lease_ids), Lease.is_deleted == False
    ).all()
    if len(leases) != len(body.lease_ids):
        raise HTTPException(status_code=400, detail="存在しない案件が含まれています")
    for lease in leases:
        if lease.status not in ("active",):
            raise HTTPException(status_code=400, detail=f"契約中の案件のみ対象です（{lease.lease_number}）")

    items = []
    for lease in leases:
        # Get area from related property (Lease model has no area_sqm)
        prop = db.query(Property).get(lease.property_id)
        area = float(prop.area_sqm) if prop and prop.area_sqm else 0.0
        result = calculate_fee(
            body.new_unit_price, area,
            lease.start_date, lease.end_date,
            body.discount_rate, body.tax_rate,
        )
        items.append({
            "lease_id": lease.id,
            "lease_number": lease.lease_number or "",
            "lessee_name": lease.lessee_name,
            "property_name": prop.name if prop else "",
            "current_annual_rent": lease.annual_rent,
            "new_total_amount": result["total_amount"],
        })

    return {"data": {"items": items, "count": len(items)}, "message": "OK"}

@router.post("/bulk-update-fee")
def bulk_update_fee(
    body: BulkFeeUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_role(user, ["admin"])

    if len(body.lease_ids) > 100:
        raise HTTPException(status_code=400, detail="対象案件は100件までです")

    leases = db.query(Lease).filter(
        Lease.id.in_(body.lease_ids), Lease.is_deleted == False
    ).all()
    if len(leases) != len(body.lease_ids):
        raise HTTPException(status_code=400, detail="存在しない案件が含まれています")
    for lease in leases:
        if lease.status not in ("active",):
            raise HTTPException(status_code=400, detail=f"契約中の案件のみ対象です（{lease.lease_number}）")

    try:
        updated_ids = []
        for lease in leases:
            # Mark old fee_details as not latest
            db.query(FeeDetail).filter(
                FeeDetail.case_id == lease.id,
                FeeDetail.case_type == "lease",
                FeeDetail.is_latest == True
            ).update({"is_latest": False})

            # Get area from related property (Lease model has no area_sqm column)
            prop = db.query(Property).get(lease.property_id)
            area = float(prop.area_sqm) if prop and prop.area_sqm else 0.0

            result = calculate_fee(
                body.new_unit_price, area,
                lease.start_date, lease.end_date,
                body.discount_rate, body.tax_rate,
            )

            fee = FeeDetail(
                case_id=lease.id, case_type="lease", is_latest=True,
                unit_price=body.new_unit_price,
                area_sqm=area,
                start_date=lease.start_date, end_date=lease.end_date,
                months=result["months"], fraction_days=result["fraction_days"],
                base_amount=result["base_amount"],
                fraction_amount=result["fraction_amount"],
                subtotal=result["subtotal"],
                discount_rate=body.discount_rate,
                discount_reason=body.discount_reason,
                discounted_amount=result["discounted_amount"],
                tax_rate=body.tax_rate,
                tax_amount=result["tax_amount"],
                total_amount=result["total_amount"],
                calculated_by=user.id, formula_version="1.0",
            )
            db.add(fee)

            old_rent = lease.annual_rent
            lease.annual_rent = result["total_amount"]
            updated_ids.append(lease.id)

            log_audit(db, user.id, "UPDATE", "t_lease", lease.id,
                      changed_fields=["annual_rent"],
                      before_value={"annual_rent": old_rent},
                      after_value={"annual_rent": result["total_amount"]},
                      ip_address=request.client.host)

        db.commit()
        return {"data": {"updated_count": len(updated_ids)}, "message": "OK"}
    except Exception:
        db.rollback()
        raise
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_bulk_fee.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routers/leases.py backend/schemas/fee.py backend/tests/test_bulk_fee.py
git commit -m "feat: add bulk fee update and preview APIs for leases"
```

### 5B: Frontend

**Files:**
- Create: `frontend/src/pages/BulkFeeUpdate.jsx`
- Modify: `frontend/src/api/leases.js`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/Layout.jsx`

- [ ] **Step 1: Add frontend API functions**

In `frontend/src/api/leases.js`:
```js
export function bulkPreviewFee(data) {
  return apiClient('/api/leases/bulk-preview', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function bulkUpdateFee(data) {
  return apiClient('/api/leases/bulk-update-fee', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 2: Create BulkFeeUpdate page**

The page has a 3-step wizard:

1. **Step 1 - Select target leases**: Table of active leases with checkboxes. Search/filter. Shows count of selected. "次へ" button when at least 1 selected.
2. **Step 2 - Set parameters**: Form with new_unit_price, discount_rate, tax_rate, discount_reason. "プレビュー" button calls `bulkPreviewFee()`.
3. **Step 3 - Preview & Confirm**: Summary table with each lease's current annual_rent vs new_total_amount (from preview response). Shows total count. "実行" button calls `bulkUpdateFee()`.
4. **Result**: Success message with updated count.

Admin-only guard at top (same pattern as MasterAdmin).

- [ ] **Step 3: Add route and nav link**

In `App.jsx`:
```jsx
<Route path="/bulk-fee-update" element={<BulkFeeUpdate />} />
```

In `Layout.jsx`: Add "一括賃料改定" nav link (admin-only, conditional render).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/BulkFeeUpdate.jsx frontend/src/api/leases.js frontend/src/App.jsx frontend/src/components/Layout.jsx
git commit -m "feat: add bulk fee update page for lease rent adjustment"
```

---

## Task 6: Final Integration & Cleanup

- [ ] **Step 1: Run all backend tests**

Run: `cd backend && pytest -v`
Expected: All tests pass

- [ ] **Step 2: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: No errors

- [ ] **Step 3: Manual smoke test**

1. Login as admin
2. Navigate to all pages, confirm no console errors
3. Test file upload on property detail
4. Test CSV export on permission list and lease list
5. Test master admin page (unit prices, user management)
6. Test bulk fee update page
7. Login as staff, confirm admin-only pages show "管理者のみアクセス可能です"
8. Login as viewer, confirm read-only pages work, write operations blocked

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final integration cleanup for missing features"
```

---

## Execution Priority

| Priority | Task | Effort | Dependencies |
|----------|------|--------|-------------|
| 1 | Task 1: Fix user role bug | Small | None |
| 2 | Task 2: File upload UI | Small | None |
| 3 | Task 3: CSV export | Medium | None |
| 4 | Task 4: Master admin page | Large | None |
| 5 | Task 5: Bulk fee update | Large | None |
| 6 | Task 6: Final integration | Small | All above |
