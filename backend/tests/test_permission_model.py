import pytest
from datetime import date
from sqlalchemy import text
from models.permission import Permission
from models.permission_history import PermissionHistory


def test_permission_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_permission)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "permission_number" in columns
    assert "property_id" in columns
    assert "parent_case_id" in columns
    assert "renewal_seq" in columns
    assert "is_latest_case" in columns
    assert "applicant_name" in columns
    assert "applicant_address" in columns
    assert "purpose" in columns
    assert "start_date" in columns
    assert "end_date" in columns
    assert "usage_area_sqm" in columns
    assert "fee_amount" in columns
    assert "override_flag" in columns
    assert "status" in columns
    assert "permission_date" in columns
    assert "is_deleted" in columns


def test_create_permission(db_session):
    perm = Permission(
        property_id=1,
        applicant_name="山田太郎",
        applicant_address="〇〇市1-1",
        purpose="イベント開催",
        start_date=date(2024, 4, 1),
        end_date=date(2024, 6, 30),
        usage_area_sqm=50.0,
    )
    db_session.add(perm)
    db_session.commit()
    db_session.refresh(perm)

    assert perm.id is not None
    assert perm.status == "draft"
    assert perm.permission_number is None  # approved時に採番
    assert perm.fee_amount is None
    assert perm.override_flag is False
    assert perm.is_deleted is False
    assert perm.renewal_seq == 0
    assert perm.is_latest_case is True
    assert perm.parent_case_id is None


def test_permission_history_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_permission_history)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "target_id" in columns
    assert "operation_type" in columns
    assert "snapshot" in columns
    assert "changed_by" in columns
    assert "reason" in columns
