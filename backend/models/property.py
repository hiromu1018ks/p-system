from datetime import date, datetime

from sqlalchemy import String, Boolean, Float, Date, DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class Property(Base):
    __tablename__ = "m_property"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str] = mapped_column(String(20), nullable=False)  # administrative / general
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    land_category: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 宅地/田/畑/山林 等
    area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
