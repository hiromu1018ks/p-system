import pytest
from sqlalchemy import text
from models.file import File


def test_file_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_file)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "related_type" in columns
    assert "related_id" in columns
    assert "file_type" in columns
    assert "original_filename" in columns
    assert "stored_path" in columns
    assert "file_size_bytes" in columns
    assert "uploaded_by" in columns
    assert "is_deleted" in columns


def test_create_file(db_session):
    f = File(
        related_type="property",
        related_id=1,
        file_type="photo",
        original_filename="公園.jpg",
        stored_path="uploads/property/1/photo_001.jpg",
        file_size_bytes=102400,
        uploaded_by=1,
    )
    db_session.add(f)
    db_session.commit()
    db_session.refresh(f)

    assert f.id is not None
    assert f.related_type == "property"
    assert f.is_deleted is False
