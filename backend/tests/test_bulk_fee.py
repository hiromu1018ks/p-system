import pytest
from datetime import date

_counter = 0


def _create_active_lease(db_session, property_type="general", sub_type="land"):
    global _counter
    _counter += 1
    from models.property import Property
    from models.lease import Lease
    prop = Property(
        property_code=f"P_BULK{_counter}",
        name="Bulk Test",
        property_type=property_type,
        area_sqm=100.0,
    )
    db_session.add(prop)
    db_session.flush()
    lease = Lease(
        property_id=prop.id, property_sub_type=sub_type,
        lessee_name="Bulk Corp", lessee_address="1-1 Test", purpose="Test purpose",
        start_date=date(2024, 4, 1), end_date=date(2025, 3, 31),
        status="active"
    )
    db_session.add(lease)
    db_session.flush()
    return lease


def test_bulk_fee_update_unauthenticated(client):
    resp = client.post("/api/leases/bulk-update-fee", json={})
    assert resp.status_code == 401


def test_bulk_fee_update_staff_denied(auth_client):
    resp = auth_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": [1], "new_unit_price": 500
    })
    assert resp.status_code == 403


def test_bulk_fee_update_success(admin_client, db_session):
    lease1 = _create_active_lease(db_session)
    lease2 = _create_active_lease(db_session)
    db_session.commit()

    resp = admin_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": [lease1.id, lease2.id],
        "new_unit_price": 500,
        "discount_rate": 0.0,
        "tax_rate": 0.10,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["updated_count"] == 2

    from models.fee_detail import FeeDetail
    for lid in [lease1.id, lease2.id]:
        fees = db_session.query(FeeDetail).filter(
            FeeDetail.case_id == lid, FeeDetail.case_type == "lease", FeeDetail.is_latest == True
        ).all()
        assert len(fees) == 1
        assert fees[0].unit_price == 500

    db_session.refresh(lease1)
    assert lease1.annual_rent is not None and lease1.annual_rent > 0


def test_bulk_fee_update_max_100(admin_client):
    ids = list(range(1, 102))
    resp = admin_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": ids, "new_unit_price": 500
    })
    assert resp.status_code in (400, 422)


def test_bulk_fee_update_non_active_fails(admin_client, db_session):
    from models.property import Property
    from models.lease import Lease
    prop = Property(property_code="P_DRAFT", name="Draft", property_type="general")
    db_session.add(prop)
    db_session.flush()
    lease = Lease(
        property_id=prop.id, property_sub_type="land",
        lessee_name="Draft Corp", lessee_address="1-1 Draft", purpose="Draft purpose",
        start_date=date(2024, 4, 1), end_date=date(2025, 3, 31),
        status="draft"
    )
    db_session.add(lease)
    db_session.commit()

    resp = admin_client.post("/api/leases/bulk-update-fee", json={
        "lease_ids": [lease.id], "new_unit_price": 500
    })
    assert resp.status_code == 400


def test_bulk_fee_preview(admin_client, db_session):
    lease = _create_active_lease(db_session)
    db_session.commit()

    resp = admin_client.post("/api/leases/bulk-preview", json={
        "lease_ids": [lease.id],
        "new_unit_price": 500,
        "discount_rate": 0.0,
        "tax_rate": 0.10,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 1
    assert data["items"][0]["lease_id"] == lease.id
    assert data["items"][0]["new_total_amount"] > 0

    from models.fee_detail import FeeDetail
    count = db_session.query(FeeDetail).filter(FeeDetail.case_id == lease.id).count()
    assert count == 0
