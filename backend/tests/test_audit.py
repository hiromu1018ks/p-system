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
