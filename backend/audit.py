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
    """監査ログを記録する。"""
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
    db.flush()
    return log
