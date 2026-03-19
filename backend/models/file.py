from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class File(Base):
    __tablename__ = "t_file"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    related_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # property / permission / lease
    related_id: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # floor_plan / photo / certificate / contract / other
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    uploaded_by: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
