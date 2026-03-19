from datetime import date, datetime

from sqlalchemy import String, Integer, Boolean, Float, Date, DateTime, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class Permission(Base):
    __tablename__ = "t_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permission_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("m_property.id"), nullable=False, index=True)
    parent_case_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("t_permission.id"), nullable=True, index=True)
    renewal_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_latest_case: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    applicant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    applicant_address: Mapped[str] = mapped_column(String(300), nullable=False)
    purpose: Mapped[str] = mapped_column(String(500), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    usage_area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    fee_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    permission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delete_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
