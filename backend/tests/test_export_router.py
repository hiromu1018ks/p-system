import pytest


def test_export_permissions_unauthenticated(client):
    resp = client.get("/api/export/permissions")
    assert resp.status_code == 401


def test_export_permissions_success(auth_client, db_session):
    from models.property import Property
    from models.permission import Permission
    from datetime import date

    prop = Property(property_code="P0001", name="Test", property_type="administrative")
    db_session.add(prop)
    db_session.commit()
    perm = Permission(
        property_id=prop.id,
        applicant_name="Test User",
        applicant_address="Tokyo",
        purpose="Testing",
        start_date=date(2024, 4, 1),
        end_date=date(2025, 3, 31),
    )
    db_session.add(perm)
    db_session.commit()

    resp = auth_client.get("/api/export/permissions")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.content
    # UTF-8 BOM check
    assert body[:3] == b"\xef\xbb\xbf"
    # Contains Japanese headers
    assert "\u8a31\u53ef\u756a\u53f7".encode("utf-8") in body


def test_export_leases_success(auth_client, db_session):
    from models.property import Property
    from models.lease import Lease
    from datetime import date

    prop = Property(property_code="P0001", name="Test", property_type="general")
    db_session.add(prop)
    db_session.commit()
    lease = Lease(
        property_id=prop.id,
        property_sub_type="land",
        lessee_name="Test Corp",
        lessee_address="Osaka",
        purpose="Office use",
        start_date=date(2024, 4, 1),
        end_date=date(2025, 3, 31),
    )
    db_session.add(lease)
    db_session.commit()

    resp = auth_client.get("/api/export/leases")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.content
    assert body[:3] == b"\xef\xbb\xbf"
    assert "\u5951\u7d04\u756a\u53f7".encode("utf-8") in body
