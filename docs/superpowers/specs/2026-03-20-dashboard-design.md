# Dashboard Design Spec

## Overview

Replace the current `DashboardPlaceholder.jsx` with a fully functional dashboard that serves as the landing page and navigation hub for the municipal property management system.

## Requirements

**Source:** Design document §4.1 (Dashboard display elements) and §6.4 (`GET /api/dashboard/summary`)

### KPI Cards (4 cards, top row)

| Card | Value | Filter | Color |
|------|-------|--------|-------|
| 使用許可案件中 | Count of in-progress permissions | `t_permission` WHERE `is_deleted=false` AND `status IN (draft, submitted, under_review, pending_approval, approved, issued)` AND `is_latest_case=true` | Blue (#2b6cb0) |
| 貸付案件中 | Count of in-progress leases | `t_lease` WHERE `is_deleted=false` AND `status IN (draft, negotiating, pending_approval, active)` AND `is_latest_case=true` | Blue (#2b6cb0) |
| 期限切れ間近 | Cases expiring within 30 days | Both tables WHERE `end_date` between today and today+30 days, `is_latest_case=true`. Permissions: exclude `expired`, `cancelled`, `rejected`. Leases: exclude `expired`, `terminated` | Red (#e53e3e) |
| 今月新規 | Cases created this month | Both tables WHERE `created_at` in current month, `is_latest_case=true` | Green (#38a169) |

### FY Total + Quick Links (second row)

- **Left:** Count of new registrations created within the current fiscal year (April 1 to present), both permissions and leases, `is_latest_case=true`, `is_deleted=false`. Display as "R{FY}年度" format.
- **Right:** 3 navigation buttons linking to Property List, Permission List, Lease List. Blue (#2b6cb0) background, white text.

### Status Distribution Chart (third row, left)

- **Chart type:** Grouped bar chart using Recharts
- **X axis:** Status names (下書き, 審査中, 決裁待ち, 承認済, 差戻し, 期間終了, etc.)
- **Y axis:** Case count
- **Two bars per status:** One for permissions (light blue), one for leases (dark blue)
- **Data source:** Count by status from both `t_permission` and `t_lease`, `is_latest_case=true`, `is_deleted=false`
- **Legend:** "使用許可" (light blue) / "普通財産貸付" (dark blue)

### Expiry Alerts (third row, right)

- List all cases where `end_date` is within 30 days from today
- Both permissions and leases, `is_latest_case=true`
- **Permissions:** exclude `expired`, `cancelled`, `rejected`
- **Leases:** exclude `expired`, `terminated`
- Sorted by remaining days ascending (most urgent first)
- **Color coding by urgency:**
  - Red (#e53e3e) + red left border: 0-7 days remaining
  - Orange (#ed8936) + orange left border: 8-15 days remaining
  - Yellow (#d69e2e) + yellow left border: 16-30 days remaining
- Each item shows: case number, applicant/lessee name, property name, remaining days
- Clicking navigates to `/permissions/{id}` or `/leases/{id}` based on `case_type`

### Recent Audit Logs (bottom, full width)

- Display the 10 most recent entries from `t_audit_log`
- Columns: 日時 (performed_at), 操作者 (user from m_user), 操作 (action), 対象 (target_table + target_id)
- **Action badge colors:**
  - CREATE → green badge
  - UPDATE → blue badge (covers both field updates and status transitions)
  - DELETE → red badge
  - PDF_GEN → purple badge

## Backend API

### `GET /api/dashboard/summary`

Single endpoint returning all dashboard data in one response. Avoids multiple round-trips.

**Response schema:**

```json
{
  "data": {
    "active_permissions": 24,
    "active_leases": 18,
    "expiring_soon": 3,
    "new_this_month": 5,
    "fy_total": 42,
    "fy_label": "R06年度",
    "status_distribution": {
      "permissions": [
        {"status": "draft", "count": 3},
        {"status": "approved", "count": 10}
      ],
      "leases": [
        {"status": "draft", "count": 2},
        {"status": "active", "count": 12}
      ]
    },
    "expiry_alerts": [
      {
        "case_type": "permission",
        "case_id": 15,
        "case_number": "R06-使-015",
        "applicant_name": "田中太郎",
        "property_name": "中央公園多功能広場",
        "end_date": "2026-03-25",
        "days_remaining": 5
      }
    ],
    "recent_logs": [
      {
        "performed_at": "2026-03-20T14:32:00+09:00",
        "user_name": "佐藤担当",
        "action": "CREATE",
        "target_table": "t_permission",
        "target_id": 15,
        "summary": "使用許可 R06-使-015"  // derived: join target_table+target_id to get case number, format as "{type_label} {number}"
      }
    ]
  }
}
```

**Router file:** `backend/routers/dashboard.py`
**Service:** Query logic inline in router (simple aggregation queries, no need for separate service file)

**`summary` field derivation (recent_logs):** Join `t_audit_log` to `m_user` for `display_name`. For `target_table` = `t_permission`, join to get `permission_number`; for `t_lease`, join to get `lease_number`; for `m_property`, join to get `property_code`. Format: `"{table_label} {identifier}"`.

## Frontend

### Files to create/modify

| File | Action |
|------|--------|
| `frontend/src/pages/Dashboard.jsx` | Create (replaces DashboardPlaceholder.jsx) |
| `frontend/src/pages/DashboardPlaceholder.jsx` | Delete |
| `frontend/src/components/StatusChart.jsx` | Create (Recharts bar chart component) |
| `frontend/src/components/ExpiryAlerts.jsx` | Create (expiry alert list component) |
| `frontend/src/components/RecentLogs.jsx` | Create (audit log table component) |
| `frontend/src/api/dashboard.js` | Create (API client for dashboard) |
| `frontend/src/App.jsx` | Modify (import Dashboard instead of DashboardPlaceholder) |

### Dependencies

- Add `recharts` to frontend (`npm install recharts`)

### Layout structure (single file `Dashboard.jsx`)

```
<header> — System title + user info + logout (same as current placeholder)
<main>
  <KPI cards row> — 4 cards in CSS grid
  <FY total + Quick links row> — 2-column grid
  <Chart + Alerts row> — 2-column grid
  <Recent logs> — full width table
</main>
```

### Styling approach

Follow existing patterns: inline styles + App.css global styles. No new CSS framework.
- KPI cards: white background, subtle box-shadow, rounded corners (border-radius: 6px)
- Alert items: colored left border, light background tint matching urgency
- Action badges: small colored pills (background + text color)

## Fiscal Year Calculation

Japanese fiscal year: April 1 to March 31.
- If current month >= April (4): FY = current year
- If current month < April: FY = current year - 1
- Display format: `R{FY % 100}年度` (e.g., 2026 → R06年度)

## Edge Cases

- **No data:** Display "データなし" in each section rather than empty space
- **Zero expiry alerts:** Show the alerts section with a green "期限切れ間近の案件はありません" message
- **Multiple users with same name:** Display `user_name` from `m_user.display_name`, joined with user_id if needed
- **is_latest_case filter:** All dashboard counts only consider the latest case in renewal chains to avoid double-counting
- **Loading state:** Show "読み込み中..." text in each section while the API call is in progress. No skeleton placeholders needed for this scale.
