import pytest
from datetime import date
from sqlalchemy import text
from models.lease import Lease
from models.lease_history import LeaseHistory


def test_lease_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_lease)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "lease_number" in columns
    assert "property_id" in columns
    assert "parent_case_id" in columns
    assert "renewal_seq" in columns
    assert "is_latest_case" in columns
    assert "lessee_name" in columns
    assert "lessee_address" in columns
    assert "purpose" in columns
    assert "start_date" in columns
    assert "end_date" in columns
    assert "property_sub_type" in columns
    assert "leased_area" in columns
    assert "annual_rent" in columns
    assert "override_flag" in columns
    assert "payment_method" in columns
    assert "status" in columns
    assert "is_deleted" in columns


def test_create_lease(db_session):
    lease = Lease(
        property_id=1,
        lessee_name="山田商事",
        lessee_address="〇〇市1-1",
        purpose="事務所として使用",
        start_date=date(2024, 4, 1),
        end_date=date(2025, 3, 31),
        property_sub_type="land",
        leased_area="100.00",
    )
    db_session.add(lease)
    db_session.commit()
    db_session.refresh(lease)

    assert lease.id is not None
    assert lease.status == "draft"
    assert lease.lease_number is None  # active時に採番
    assert lease.annual_rent is None
    assert lease.override_flag is False
    assert lease.is_deleted is False
    assert lease.renewal_seq == 0
    assert lease.is_latest_case is True
    assert lease.parent_case_id is None


def test_lease_history_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_lease_history)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "target_id" in columns
    assert "operation_type" in columns
    assert "snapshot" in columns
    assert "changed_by" in columns
    assert "reason" in columns
