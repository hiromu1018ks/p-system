from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class LeaseHistory(Base):
    __tablename__ = "t_lease_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    operation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # CREATE / UPDATE / STATUS_CHANGE / DELETE / RESTORE
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    changed_by: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
