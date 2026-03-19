import pytest
from datetime import date
from decimal import Decimal
from services.fee_calculator import calculate_fee


class TestCalculateFeeBasic:
    """§2.6.1 7段階計算の基本テスト"""

    def test_full_months_no_discount_no_tax(self):
        """2ヶ月、減免なし、非課税"""
        result = calculate_fee(
            unit_price=320,
            area_sqm=50.0,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 5, 31),
            discount_rate=0.0,
            tax_rate=0.0,
        )
        assert result["months"] == 2
        assert result["fraction_days"] == 0
        assert result["base_amount"] == 32000  # 320 * 50 * 2
        assert result["fraction_amount"] == 0
        assert result["subtotal"] == 32000
        assert result["discounted_amount"] == 32000
        assert result["tax_amount"] == 0
        assert result["total_amount"] == 32000

    def test_full_months_with_tax(self):
        """2ヶ月、10%消費税"""
        result = calculate_fee(
            unit_price=320,
            area_sqm=50.0,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 5, 31),
            discount_rate=0.0,
            tax_rate=0.10,
        )
        assert result["subtotal"] == 32000
        assert result["tax_amount"] == 3200
        assert result["total_amount"] == 35200

    def test_fraction_days_calculation(self):
        """2ヶ月 + 15日（端月日割り）"""
        result = calculate_fee(
            unit_price=320,
            area_sqm=50.0,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 6, 15),
            discount_rate=0.0,
            tax_rate=0.10,
        )
        assert result["months"] == 2
        assert result["fraction_days"] == 15
        assert result["base_amount"] == 32000
        # 日割: 320 * 50 * 15 / 31 = 7741.935... → 切り捨て = 7741
        assert result["fraction_amount"] == 7741
        assert result["subtotal"] == 39741
        # discounted_amount = floor(39741 * 1.0) = 39741
        # tax_amount = floor(39741 * 0.10) = 3974
        # total = 39741 + 3974 = 43715
        assert result["total_amount"] == 43715

    def test_discount_30_percent(self):
        """30%減免"""
        result = calculate_fee(
            unit_price=320,
            area_sqm=50.0,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 5, 31),
            discount_rate=0.3,
            tax_rate=0.10,
        )
        # subtotal = 32000
        # discounted = floor(32000 * 0.7) = 22400
        assert result["discounted_amount"] == 22400
        assert result["tax_amount"] == 2240
        assert result["total_amount"] == 24640

    def test_fraction_rounding_down(self):
        """端数は円未満切り捨て（条例準拠）"""
        result = calculate_fee(
            unit_price=300,
            area_sqm=100.0,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 20),
            discount_rate=0.0,
            tax_rate=0.10,
        )
        assert result["months"] == 0
        assert result["fraction_days"] == 20
        # 日割: 300 * 100 * 20 / 30 = 20000（割り切れる）
        assert result["fraction_amount"] == 20000


class TestCalculateFeeEdgeCases:
    def test_single_day(self):
        """1日のみの利用"""
        result = calculate_fee(
            unit_price=500,
            area_sqm=10.0,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 15),
            discount_rate=0.0,
            tax_rate=0.0,
        )
        assert result["months"] == 0
        assert result["fraction_days"] == 1
        assert result["fraction_amount"] == 5000 // 30  # floor(5000/30) = 166

    def test_full_year(self):
        """1年間（12ヶ月）"""
        result = calculate_fee(
            unit_price=100,
            area_sqm=100.0,
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            discount_rate=0.0,
            tax_rate=0.0,
        )
        assert result["months"] == 12
        assert result["fraction_days"] == 0
        assert result["base_amount"] == 120000

    def test_across_month_boundary(self):
        """月をまたぐ場合"""
        result = calculate_fee(
            unit_price=200,
            area_sqm=50.0,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 5, 14),
            discount_rate=0.0,
            tax_rate=0.0,
        )
        assert result["months"] == 0
        assert result["fraction_days"] == 30  # 16(4月) + 14(5月) = 30日
        assert result["total_amount"] >= 0
