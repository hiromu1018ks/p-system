import pytest
from datetime import date
from sqlalchemy import text
from models.fee_detail import FeeDetail
from models.unit_price import UnitPrice


def test_fee_detail_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_fee_detail)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "case_id" in columns
    assert "case_type" in columns
    assert "is_latest" in columns
    assert "unit_price" in columns
    assert "area_sqm" in columns
    assert "base_amount" in columns
    assert "total_amount" in columns
    assert "formula_version" in columns


def test_create_fee_detail(db_session):
    fee = FeeDetail(
        case_id=1,
        case_type="permission",
        unit_price=320,
        area_sqm=50.0,
        start_date=date(2024, 4, 1),
        end_date=date(2024, 6, 30),
        months=3,
        fraction_days=0,
        base_amount=48000,
        fraction_amount=0,
        subtotal=48000,
        discount_rate=0.0,
        discounted_amount=48000,
        tax_rate=0.10,
        tax_amount=4800,
        total_amount=52800,
        calculated_by=1,
        formula_version="1.0",
    )
    db_session.add(fee)
    db_session.commit()
    db_session.refresh(fee)

    assert fee.id is not None
    assert fee.is_latest is True
    assert fee.total_amount == 52800


def test_unit_price_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(m_unit_price)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "property_type" in columns
    assert "usage" in columns
    assert "unit_price" in columns
    assert "start_date" in columns
    assert "end_date" in columns


def test_create_unit_price(db_session):
    up = UnitPrice(
        property_type="administrative",
        usage="公園使用",
        unit_price=320,
        start_date=date(2024, 4, 1),
    )
    db_session.add(up)
    db_session.commit()
    db_session.refresh(up)

    assert up.id is not None
    assert up.end_date is None  # 現在適用中
