import pytest
from services.pdf_generator import generate_pdf


def test_generate_permission_certificate(tmp_path):
    case_data = {
        "permission_number": "R06-使-001",
        "applicant_name": "山田太郎",
        "applicant_address": "〇〇市1-1-1",
        "property_name": "市民公園",
        "property_address": "〇〇市〇〇町1-1",
        "purpose": "イベント開催",
        "start_date": "2024-04-01",
        "end_date": "2024-06-30",
        "usage_area_sqm": "50.00",
        "fee_amount": 30000,
        "conditions": "使用時間は9:00〜17:00とする",
        "permission_date": "2024-04-01",
    }
    output_path = tmp_path / "test_permission.pdf"
    result = generate_pdf("permission_certificate", case_data, str(output_path))
    assert result == str(output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_land_lease_contract(tmp_path):
    case_data = {
        "lease_number": "R06-貸-001",
        "property_name": "市有地",
        "property_address": "〇〇市〇〇町1-1",
        "property_lot_number": "1-1-1",
        "property_area": "100.00",
        "lessee_name": "山田商事株式会社",
        "lessee_address": "〇〇市1-1-1",
        "purpose": "駐車場として使用",
        "start_date": "2024-04-01",
        "end_date": "2025-03-31",
        "annual_rent": 120000,
        "payment_method": "monthly",
        "approval_date": "2024-03-25",
    }
    output_path = tmp_path / "test_land_lease.pdf"
    result = generate_pdf("land_lease_contract", case_data, str(output_path))
    assert result == str(output_path)
    assert output_path.exists()


def test_generate_building_lease_contract(tmp_path):
    case_data = {
        "lease_number": "R06-貸-002",
        "property_name": "市有施設",
        "property_address": "〇〇市〇〇町2-1",
        "lessee_name": "田中商店",
        "lessee_address": "〇〇市2-1-1",
        "purpose": "店舗として使用",
        "start_date": "2024-04-01",
        "end_date": "2025-03-31",
        "annual_rent": 600000,
        "payment_method": "monthly",
        "approval_date": "2024-03-25",
    }
    output_path = tmp_path / "test_building_lease.pdf"
    result = generate_pdf("building_lease_contract", case_data, str(output_path))
    assert result == str(output_path)
    assert output_path.exists()


def test_generate_renewal_notice(tmp_path):
    case_data = {
        "case_type": "permission",
        "case_number": "R06-使-001",
        "applicant_name": "山田太郎",
        "applicant_address": "〇〇市1-1-1",
        "purpose": "イベント開催",
        "current_end_date": "2024-06-30",
        "new_start_date": "2024-07-01",
        "new_end_date": "2025-06-30",
        "new_fee": 36000,
        "renewal_deadline": "2024-06-01",
    }
    output_path = tmp_path / "test_renewal.pdf"
    result = generate_pdf("renewal_notice", case_data, str(output_path))
    assert result == str(output_path)
    assert output_path.exists()


def test_generate_pdf_invalid_type(tmp_path):
    with pytest.raises(ValueError):
        generate_pdf("invalid_type", {}, str(tmp_path / "test.pdf"))
