import pytest
from sqlalchemy import text
from models.document import Document


def test_document_table_exists(db_session):
    result = db_session.execute(text("PRAGMA table_info(t_document)"))
    columns = {row[1] for row in result}
    assert "id" in columns
    assert "case_id" in columns
    assert "case_type" in columns
    assert "document_type" in columns
    assert "file_path" in columns
    assert "generated_by" in columns


def test_create_document(db_session):
    doc = Document(
        case_id=1,
        case_type="permission",
        document_type="permission_certificate",
        file_path="generated_pdfs/test.pdf",
        generated_by=1,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert doc.case_type == "permission"
    assert doc.document_type == "permission_certificate"
