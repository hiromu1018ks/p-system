from datetime import date, datetime

from sqlalchemy import String, Integer, Boolean, Float, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class FeeDetail(Base):
    __tablename__ = "t_fee_detail"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    case_type: Mapped[str] = mapped_column(String(20), nullable=False)  # permission / lease
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 円/㎡/月
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False)  # ㎡
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    months: Mapped[int] = mapped_column(Integer, nullable=False)
    fraction_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    base_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 円
    fraction_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 円
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)  # 円
    discount_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    discounted_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 円
    tax_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 円
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 円
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    calculated_by: Mapped[int] = mapped_column(Integer, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
