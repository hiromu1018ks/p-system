import json

import pytest
from sqlalchemy import text

from models.property import Property
from models.property_history import PropertyHistory


def test_property_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(m_property)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "property_code" in columns
    assert "name" in columns
    assert "property_type" in columns
    assert "address" in columns
    assert "lot_number" in columns
    assert "land_category" in columns
    assert "area_sqm" in columns
    assert "acquisition_date" in columns
    assert "latitude" in columns
    assert "longitude" in columns
    assert "remarks" in columns
    assert "is_deleted" in columns


def test_create_property(db_session):
    prop = Property(
        property_code="P0001",
        name="市民公園",
        property_type="administrative",
        address="〇〇市〇〇町1-1",
        lot_number="1-1-1",
        land_category="宅地",
        area_sqm=1500.50,
        latitude=35.6812,
        longitude=139.7671,
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    assert prop.id is not None
    assert prop.property_code == "P0001"
    assert prop.property_type == "administrative"
    assert prop.area_sqm == 1500.50
    assert prop.is_deleted is False


def test_property_default_values(db_session):
    prop = Property(
        property_code="P0002",
        name="テスト財産",
        property_type="general",
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    assert prop.is_deleted is False
    assert prop.address is None
    assert prop.latitude is None
    assert prop.remarks is None


def test_property_history_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(m_property_history)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "target_id" in columns
    assert "operation_type" in columns
    assert "snapshot" in columns
    assert "changed_by" in columns
    assert "reason" in columns


def test_create_property_history(db_session):
    prop = Property(
        property_code="P0003",
        name="テスト財産",
        property_type="administrative",
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)

    history = PropertyHistory(
        target_id=prop.id,
        operation_type="CREATE",
        snapshot=json.dumps({
            "property_code": "P0003",
            "name": "テスト財産",
            "property_type": "administrative",
        }, ensure_ascii=False),
        changed_by=1,
        reason="新規登録",
    )
    db_session.add(history)
    db_session.commit()
    db_session.refresh(history)

    assert history.id is not None
    assert history.target_id == prop.id
    assert history.operation_type == "CREATE"
