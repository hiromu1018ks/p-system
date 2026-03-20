from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class Document(Base):
    __tablename__ = "t_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    case_type: Mapped[str] = mapped_column(String(20), nullable=False)  # permission / lease
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # permission_certificate / land_lease_contract / building_lease_contract / renewal_notice
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_by: Mapped[int] = mapped_column(Integer, nullable=False)
