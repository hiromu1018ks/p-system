import calendar
from datetime import date
from decimal import Decimal, ROUND_DOWN


FORMULA_VERSION = "1.0"


def calculate_fee(
    unit_price: int,
    area_sqm: float,
    start_date: date,
    end_date: date,
    discount_rate: float = 0.0,
    tax_rate: float = 0.10,
) -> dict:
    """§2.6.1 7段階料金計算

    ① 基本料金 = 単価 × 面積 × 使用月数
    ② 日割調整 = 端月の日割り計算（暦日で除す）
    ③ 小計 = ① + ②
    ④ 減免適用 = 小計 × (1 - 減額率)
    ⑤ 税抜金額 = ④の端数処理（円未満切り捨て）
    ⑥ 消費税 = ⑤ × 税率（円未満切り捨て）
    ⑦ 税込合計 = ⑤ + ⑥

    全金額は INTEGER（円単位）。中間計算は Decimal で精度保証。
    """
    up = Decimal(str(unit_price))
    area = Decimal(str(area_sqm))
    dr = Decimal(str(discount_rate))
    tr = Decimal(str(tax_rate))

    months, fraction_days, fraction_amount = _calculate_periods(up, area, start_date, end_date)

    # ① 基本料金
    base_amount = int(up * area * months)

    # ③ 小計
    subtotal = base_amount + fraction_amount

    # ④⑤ 減免適用 + 端数処理
    discounted_amount = int((Decimal(subtotal) * (Decimal("1") - dr)).to_integral_value(rounding=ROUND_DOWN))

    # ⑥ 消費税
    tax_amount = int((Decimal(discounted_amount) * tr).to_integral_value(rounding=ROUND_DOWN))

    # ⑦ 税込合計
    total_amount = discounted_amount + tax_amount

    return {
        "unit_price": unit_price,
        "area_sqm": area_sqm,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "months": months,
        "fraction_days": fraction_days,
        "base_amount": base_amount,
        "fraction_amount": fraction_amount,
        "subtotal": subtotal,
        "discount_rate": float(dr),
        "discounted_amount": discounted_amount,
        "tax_rate": float(tr),
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "formula_version": FORMULA_VERSION,
    }


def _calculate_periods(
    unit_price: Decimal,
    area: Decimal,
    start_date: date,
    end_date: date,
) -> tuple[int, int, int]:
    """月数・端数日数・日割金額を計算する

    日割り計算の除数（基準日数）:
    - 直前の完全月がある場合は、その月の日数を使用
    - 完全月がない場合は、端月自身の日数を使用

    Returns:
        (months, fraction_days, fraction_amount)
    """
    months = 0
    fraction_days = 0
    fraction_amount = 0
    last_full_month_days = None  # 直前の完全月の日数

    current = start_date
    while current <= end_date:
        days_in_month = calendar.monthrange(current.year, current.month)[1]

        if current.month == end_date.month and current.year == end_date.year:
            # 最終月
            days_used = end_date.day - current.day + 1
            if days_used == days_in_month and current.day == 1:
                # 月初から月末まで = 完全な1ヶ月
                months += 1
                last_full_month_days = days_in_month
            elif days_used == days_in_month:
                # 月の途中から月末まで = 完全な残月
                months += 1
                last_full_month_days = days_in_month
            else:
                # 端月
                fraction_days += days_used
                # 直前の完全月の日数があればそれを使用、なければ当月の日数
                divisor = last_full_month_days if last_full_month_days is not None else days_in_month
                fraction_amount += int(
                    (unit_price * area * Decimal(days_used) / Decimal(divisor))
                    .to_integral_value(rounding=ROUND_DOWN)
                )
        elif current.day == 1:
            # 月初から = 完全な1ヶ月（最終月でない）
            months += 1
            last_full_month_days = days_in_month
            # 月末まで進める
            next_month = (current.month % 12) + 1
            next_year = current.year + (1 if current.month == 12 else 0)
            current = date(next_year, next_month, 1)
            continue
        else:
            # 月の途中から開始 = 端月
            days_used = days_in_month - current.day + 1
            fraction_days += days_used
            # 直前の完全月の日数があればそれを使用、なければ当月の日数
            divisor = last_full_month_days if last_full_month_days is not None else days_in_month
            fraction_amount += int(
                (unit_price * area * Decimal(days_used) / Decimal(divisor))
                .to_integral_value(rounding=ROUND_DOWN)
            )

        # 次の月へ
        next_month = (current.month % 12) + 1
        next_year = current.year + (1 if current.month == 12 else 0)
        current = date(next_year, next_month, 1)

    return months, fraction_days, fraction_amount
