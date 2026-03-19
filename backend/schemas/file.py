from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    related_type: str
    related_id: int
    file_type: str
    original_filename: str
    file_size_bytes: int
    uploaded_at: datetime | None
    uploaded_by: int

    model_config = {"from_attributes": True}
