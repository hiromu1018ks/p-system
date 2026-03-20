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
