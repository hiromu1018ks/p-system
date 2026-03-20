import json
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.lease import Lease
from models.lease_history import LeaseHistory
from audit import log_audit


def generate_lease_number(db: Session, approval_date: date) -> str:
    """契約番号を自動採番する（§2.5.2）

    format: R{年度2桁}-貸-{3桁連番}
    年度跨ぎ対応: 4月開始年度。年度ごとにリセット。
    """
    fy_year = approval_date.year if approval_date.month >= 4 else approval_date.year - 1
    fy_str = f"{fy_year % 100:02d}"
    prefix = f"R{fy_str}-貸-"

    latest = (
        db.query(Lease)
        .filter(Lease.lease_number.like(f"{prefix}%"))
        .order_by(Lease.lease_number.desc())
        .first()
    )

    if latest and latest.lease_number:
        try:
            seq = int(latest.lease_number[-3:]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"


def create_lease(db: Session, data: dict, user_id: int, ip_address: str | None = None) -> Lease:
    """貸付案件を新規登録する"""
    lease = Lease(**data)
    db.add(lease)
    db.flush()

    _save_history(db, lease, "CREATE", user_id, "新規登録")
    _log_audit(db, user_id, "CREATE", lease.id, list(data.keys()), after=_to_snapshot(lease), ip=ip_address)

    db.commit()
    db.refresh(lease)
    return lease


def update_lease(db: Session, lease: Lease, data: dict, user_id: int, ip_address: str | None = None) -> Lease:
    """貸付案件を更新する"""
    before = _to_snapshot(lease)
    changed_fields = []

    for key, value in data.items():
        if value is not None and getattr(lease, key, None) != value:
            changed_fields.append(key)
            setattr(lease, key, value)

    if not changed_fields:
        return lease

    db.flush()
    after = _to_snapshot(lease)

    _save_history(db, lease, "UPDATE", user_id, "更新")
    _log_audit(db, user_id, "UPDATE", lease.id, changed_fields, before=before, after=after, ip=ip_address)

    db.commit()
    db.refresh(lease)
    return lease


def delete_lease(db: Session, lease: Lease, user_id: int, ip_address: str | None = None, reason: str = "削除") -> Lease:
    """貸付案件を論理削除する"""
    lease.is_deleted = True
    lease.delete_reason = reason

    _save_history(db, lease, "DELETE", user_id, reason)
    _log_audit(db, user_id, "DELETE", lease.id, ["is_deleted"], before={"is_deleted": False}, after={"is_deleted": True}, ip=ip_address)

    db.commit()
    db.refresh(lease)
    return lease


def list_leases(db: Session, q: str | None = None, status: str | None = None, page: int = 1, per_page: int = 20) -> tuple[list[Lease], int]:
    """貸付案件一覧を取得する（ページング付き）"""
    query = db.query(Lease).filter(Lease.is_deleted == False)

    if q:
        query = query.filter(
            or_(
                Lease.lessee_name.contains(q),
                Lease.purpose.contains(q),
                Lease.lease_number.contains(q),
            )
        )

    if status:
        query = query.filter(Lease.status == status)

    total = query.count()
    items = query.order_by(Lease.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_lease_history(db: Session, lease_id: int) -> list[LeaseHistory]:
    """貸付案件の変更履歴を取得する"""
    return db.query(LeaseHistory).filter(
        LeaseHistory.target_id == lease_id
    ).order_by(LeaseHistory.changed_at.desc()).all()


def change_status(
    db: Session,
    lease: Lease,
    new_status: str,
    user_id: int,
    reason: str,
    expected_current_status: str,
    expected_updated_at: datetime,
    ip_address: str | None = None,
) -> Lease:
    """ステータスを変更する（楽観ロック付き）"""

    # 楽観ロックチェック
    if lease.status != expected_current_status:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "OPTIMISTIC_LOCK_CONFLICT",
            "message": "他のユーザーが変更しました。画面を再読み込みしてください。",
            "detail": {"current": lease.status, "expected": expected_current_status},
        })

    if lease.updated_at.replace(tzinfo=None) != expected_updated_at.replace(tzinfo=None):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "OPTIMISTIC_LOCK_CONFLICT",
            "message": "他のユーザーが変更しました。画面を再読み込みしてください。",
            "detail": {"current": str(lease.updated_at), "expected": str(expected_updated_at)},
        })

    # 遷移チェック
    from services.status_machine import is_valid_transition
    if not is_valid_transition("lease", lease.status, new_status):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "INVALID_STATUS_TRANSITION",
            "message": f"{lease.status} から {new_status} への遷移は許可されていません",
            "detail": {"current": lease.status, "requested": new_status},
        })

    before = _to_snapshot(lease)
    lease.status = new_status

    # active に遷移した場合、契約番号を採番
    if new_status == "active":
        today = date.today()
        lease.lease_number = generate_lease_number(db, today)

    db.flush()
    after = _to_snapshot(lease)

    _save_history(db, lease, "STATUS_CHANGE", user_id, reason)
    _log_audit(
        db, user_id, "UPDATE", lease.id,
        changed_fields=["status"],
        before=before, after=after, ip=ip_address,
    )

    db.commit()
    db.refresh(lease)
    return lease


def start_renewal(
    db: Session,
    lease: Lease,
    user_id: int,
    reason: str | None = None,
    ip_address: str | None = None,
) -> Lease:
    """更新手続きを開始する（§2.3 更新モデル）"""
    allowed = ("active", "expired")
    if lease.status not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "INVALID_RENEWAL_STATUS",
            "message": f"{lease.status} の案件は更新できません",
        })

    root_id = lease.parent_case_id if lease.parent_case_id else lease.id

    # 現行レコードの is_latest_case を false に更新
    db.query(Lease).filter(
        Lease.parent_case_id == root_id if lease.parent_case_id else Lease.id == root_id,
        Lease.is_latest_case == True,
    ).update({"is_latest_case": False})

    new_lease = Lease(
        property_id=lease.property_id,
        parent_case_id=root_id,
        renewal_seq=lease.renewal_seq + 1,
        is_latest_case=True,
        property_sub_type=lease.property_sub_type,
        lessee_name=lease.lessee_name,
        lessee_address=lease.lessee_address,
        lessee_contact=lease.lessee_contact,
        purpose=lease.purpose,
        start_date=lease.start_date,
        end_date=lease.end_date,
        leased_area=lease.leased_area,
        payment_method=lease.payment_method,
        status="draft",
    )
    db.add(new_lease)
    db.flush()

    _save_history(db, new_lease, "CREATE", user_id, reason or "更新手続き開始")
    _log_audit(db, user_id, "CREATE", new_lease.id, ["renewal_from"], after={"renewal_from": lease.id}, ip=ip_address)

    db.commit()
    db.refresh(new_lease)
    return new_lease


def _to_snapshot(lease: Lease) -> dict:
    return {
        "lease_number": lease.lease_number,
        "property_id": lease.property_id,
        "parent_case_id": lease.parent_case_id,
        "renewal_seq": lease.renewal_seq,
        "is_latest_case": lease.is_latest_case,
        "property_sub_type": lease.property_sub_type,
        "lessee_name": lease.lessee_name,
        "lessee_address": lease.lessee_address,
        "lessee_contact": lease.lessee_contact,
        "purpose": lease.purpose,
        "start_date": str(lease.start_date),
        "end_date": str(lease.end_date),
        "leased_area": lease.leased_area,
        "annual_rent": lease.annual_rent,
        "override_flag": lease.override_flag,
        "payment_method": lease.payment_method,
        "status": lease.status,
    }


def _save_history(db: Session, lease: Lease, operation_type: str, user_id: int, reason: str | None):
    history = LeaseHistory(
        target_id=lease.id,
        operation_type=operation_type,
        snapshot=json.dumps(_to_snapshot(lease), ensure_ascii=False),
        changed_by=user_id,
        reason=reason,
    )
    db.add(history)


def _log_audit(db: Session, user_id: int, action: str, target_id: int, changed_fields: list, before=None, after=None, ip=None):
    log_audit(
        db=db,
        user_id=user_id,
        action=action,
        target_table="t_lease",
        target_id=target_id,
        changed_fields=changed_fields,
        before_value=before,
        after_value=after,
        ip_address=ip,
    )
