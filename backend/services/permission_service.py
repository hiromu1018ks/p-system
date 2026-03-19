import json
import calendar
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models.permission import Permission
from models.permission_history import PermissionHistory
from audit import log_audit


def generate_permission_number(db: Session, permission_date: date) -> str:
    """許可番号を自動採番する（§2.5.1）

    format: R{年度2桁}-使-{3桁連番}
    年度跨ぎ対応: 4月開始年度。年度ごとにリセット。
    """
    # 年度計算: 4月開始
    fy_year = permission_date.year if permission_date.month >= 4 else permission_date.year - 1
    fy_str = f"{fy_year % 100:02d}"
    prefix = f"R{fy_str}-使-"

    # 同じプレフィックスの最新番号を取得
    latest = (
        db.query(Permission)
        .filter(Permission.permission_number.like(f"{prefix}%"))
        .order_by(Permission.permission_number.desc())
        .first()
    )

    if latest and latest.permission_number:
        try:
            seq = int(latest.permission_number[-3:]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"


def create_permission(db: Session, data: dict, user_id: int, ip_address: str | None = None) -> Permission:
    """使用許可案件を新規登録する"""
    perm = Permission(**data)
    db.add(perm)
    db.flush()

    _save_history(db, perm, "CREATE", user_id, "新規登録")
    _log_audit(db, user_id, "CREATE", perm.id, list(data.keys()), after=_to_snapshot(perm), ip=ip_address)

    db.commit()
    db.refresh(perm)
    return perm


def update_permission(db: Session, perm: Permission, data: dict, user_id: int, ip_address: str | None = None) -> Permission:
    """使用許可案件を更新する"""
    before = _to_snapshot(perm)
    changed_fields = []

    for key, value in data.items():
        if value is not None and getattr(perm, key, None) != value:
            changed_fields.append(key)
            setattr(perm, key, value)

    if not changed_fields:
        return perm

    db.flush()
    after = _to_snapshot(perm)

    _save_history(db, perm, "UPDATE", user_id, "更新")
    _log_audit(db, user_id, "UPDATE", perm.id, changed_fields, before=before, after=after, ip=ip_address)

    db.commit()
    db.refresh(perm)
    return perm


def delete_permission(db: Session, perm: Permission, user_id: int, ip_address: str | None = None, reason: str = "削除") -> Permission:
    """使用許可案件を論理削除する"""
    perm.is_deleted = True
    perm.delete_reason = reason

    _save_history(db, perm, "DELETE", user_id, reason)
    _log_audit(db, user_id, "DELETE", perm.id, ["is_deleted"], before={"is_deleted": False}, after={"is_deleted": True}, ip=ip_address)

    db.commit()
    db.refresh(perm)
    return perm


def list_permissions(db: Session, q: str | None = None, status: str | None = None, page: int = 1, per_page: int = 20) -> tuple[list[Permission], int]:
    """使用許可案件一覧を取得する（ページング付き）"""
    query = db.query(Permission).filter(Permission.is_deleted == False)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Permission.applicant_name.contains(q),
                Permission.purpose.contains(q),
                Permission.permission_number.contains(q),
            )
        )

    if status:
        query = query.filter(Permission.status == status)

    total = query.count()
    items = query.order_by(Permission.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_permission_history(db: Session, permission_id: int) -> list[PermissionHistory]:
    """使用許可案件の変更履歴を取得する"""
    return db.query(PermissionHistory).filter(
        PermissionHistory.target_id == permission_id
    ).order_by(PermissionHistory.changed_at.desc()).all()


def change_status(
    db: Session,
    perm: Permission,
    new_status: str,
    user_id: int,
    reason: str,
    expected_current_status: str,
    expected_updated_at: datetime,
    ip_address: str | None = None,
) -> Permission:
    """ステータスを変更する（楽観ロック付き）"""

    # 楽観ロックチェック
    if perm.status != expected_current_status:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "OPTIMISTIC_LOCK_CONFLICT",
            "message": "他のユーザーが変更しました。画面を再読み込みしてください。",
            "detail": {"current": perm.status, "expected": expected_current_status},
        })

    if perm.updated_at.replace(tzinfo=None) != expected_updated_at.replace(tzinfo=None):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "OPTIMISTIC_LOCK_CONFLICT",
            "message": "他のユーザーが変更しました。画面を再読み込みしてください。",
            "detail": {"current": str(perm.updated_at), "expected": str(expected_updated_at)},
        })

    # 遷移チェック
    from services.status_machine import is_valid_transition
    if not is_valid_transition("permission", perm.status, new_status):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "INVALID_STATUS_TRANSITION",
            "message": f"{perm.status} から {new_status} への遷移は許可されていません",
            "detail": {"current": perm.status, "requested": new_status},
        })

    before = _to_snapshot(perm)
    perm.status = new_status

    # approved に遷移した場合、許可番号を採番 + 許可年月日を設定
    if new_status == "approved":
        from datetime import date
        today = date.today()
        perm.permission_number = generate_permission_number(db, today)
        perm.permission_date = today

    db.flush()
    after = _to_snapshot(perm)

    _save_history(db, perm, "STATUS_CHANGE", user_id, reason)
    _log_audit(
        db, user_id, "UPDATE", perm.id,
        changed_fields=["status"],
        before=before, after=after, ip=ip_address,
    )

    db.commit()
    db.refresh(perm)
    return perm


def start_renewal(
    db: Session,
    perm: Permission,
    user_id: int,
    reason: str | None = None,
    ip_address: str | None = None,
) -> Permission:
    """更新手続きを開始する（§2.3 更新モデル）

    現行レコードは変更せず、新レコード(draft)を作成する。
    parent_case_id は常に初回IDを指す。
    """
    # 許可されるステータス: approved, issued, expired
    allowed = ("approved", "issued", "expired")
    if perm.status not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={
            "code": "INVALID_RENEWAL_STATUS",
            "message": f"{perm.status} の案件は更新できません",
        })

    # parent_case_id は初回ID（チェーンのルート）を指す
    root_id = perm.parent_case_id if perm.parent_case_id else perm.id

    # 現行レコードの is_latest_case を false に更新
    db.query(Permission).filter(
        Permission.parent_case_id == root_id if perm.parent_case_id else Permission.id == root_id,
        Permission.is_latest_case == True,
    ).update({"is_latest_case": False})

    # 新レコードを作成
    new_perm = Permission(
        property_id=perm.property_id,
        parent_case_id=root_id,
        renewal_seq=perm.renewal_seq + 1,
        is_latest_case=True,
        applicant_name=perm.applicant_name,
        applicant_address=perm.applicant_address,
        purpose=perm.purpose,
        start_date=perm.start_date,  # 初期値としてコピー（後で変更される）
        end_date=perm.end_date,
        usage_area_sqm=perm.usage_area_sqm,
        conditions=perm.conditions,
        status="draft",
    )
    db.add(new_perm)
    db.flush()

    _save_history(db, new_perm, "CREATE", user_id, reason or "更新手続き開始")
    _log_audit(db, user_id, "CREATE", new_perm.id, ["renewal_from"], after={"renewal_from": perm.id}, ip=ip_address)

    db.commit()
    db.refresh(new_perm)
    return new_perm


def _to_snapshot(perm: Permission) -> dict:
    return {
        "permission_number": perm.permission_number,
        "property_id": perm.property_id,
        "parent_case_id": perm.parent_case_id,
        "renewal_seq": perm.renewal_seq,
        "is_latest_case": perm.is_latest_case,
        "applicant_name": perm.applicant_name,
        "applicant_address": perm.applicant_address,
        "purpose": perm.purpose,
        "start_date": str(perm.start_date),
        "end_date": str(perm.end_date),
        "usage_area_sqm": str(perm.usage_area_sqm) if perm.usage_area_sqm else None,
        "fee_amount": perm.fee_amount,
        "override_flag": perm.override_flag,
        "conditions": perm.conditions,
        "status": perm.status,
        "permission_date": str(perm.permission_date) if perm.permission_date else None,
    }


def _save_history(db: Session, perm: Permission, operation_type: str, user_id: int, reason: str | None):
    history = PermissionHistory(
        target_id=perm.id,
        operation_type=operation_type,
        snapshot=json.dumps(_to_snapshot(perm), ensure_ascii=False),
        changed_by=user_id,
        reason=reason,
    )
    db.add(history)


def _log_audit(db: Session, user_id: int, action: str, target_id: int, changed_fields: list, before=None, after=None, ip=None):
    log_audit(
        db=db,
        user_id=user_id,
        action=action,
        target_table="t_permission",
        target_id=target_id,
        changed_fields=changed_fields,
        before_value=before,
        after_value=after,
        ip_address=ip,
    )
