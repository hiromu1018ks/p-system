from datetime import date, datetime

from sqlalchemy import String, Integer, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class UnitPrice(Base):
    __tablename__ = "m_unit_price"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_type: Mapped[str] = mapped_column(String(20), nullable=False)  # administrative / general
    usage: Mapped[str] = mapped_column(String(100), nullable=False)  # 用途
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 円/㎡/月
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # NULL = 現在適用中
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
