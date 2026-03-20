import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.user import User
from models.file import File as FileModel
from audit import log_audit

router = APIRouter(prefix="/api/files", tags=["files"])

UPLOAD_DIR = "uploads"


@router.post("/upload", status_code=201)
async def upload_file(
    related_type: str = Form(...),
    related_id: int = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if related_type not in ("property", "permission", "lease"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_RELATED_TYPE", "message": "無効な関連タイプです"},
        )

    if file_type not in ("floor_plan", "photo", "certificate", "contract", "other"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FILE_TYPE", "message": "無効なファイル種別です"},
        )

    # 関連エンティティの存在チェック（§5.4要件）
    if related_type == "property":
        from models.property import Property
        entity = db.query(Property).filter(Property.id == related_id).first()
        if not entity:
            raise HTTPException(
                status_code=404,
                detail={"code": "PROPERTY_NOT_FOUND", "message": "関連する財産が見つかりません"},
            )
    elif related_type == "permission":
        from models.permission import Permission
        entity = db.query(Permission).filter(Permission.id == related_id).first()
        if not entity:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERMISSION_NOT_FOUND", "message": "関連する使用許可案件が見つかりません"},
            )

    # 保存ディレクトリ作成
    save_dir = os.path.join(UPLOAD_DIR, related_type, str(related_id), file_type)
    os.makedirs(save_dir, exist_ok=True)

    # 一意のファイル名を生成
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(save_dir, stored_name)

    # ファイル保存
    content = await file.read()
    with open(stored_path, "wb") as f:
        f.write(content)

    # DB記録
    file_record = FileModel(
        related_type=related_type,
        related_id=related_id,
        file_type=file_type,
        original_filename=file.filename or "unknown",
        stored_path=stored_path,
        file_size_bytes=len(content),
        uploaded_by=current_user.id,
    )
    db.add(file_record)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        target_table="t_file",
        target_id=file_record.id,
        changed_fields=["related_type", "related_id", "file_type", "original_filename"],
        after_value={
            "related_type": related_type,
            "related_id": related_id,
            "file_type": file_type,
            "original_filename": file.filename,
        },
    )

    db.commit()
    db.refresh(file_record)
    return {"data": file_record, "message": "ファイルをアップロードしました"}


@router.get("")
def list_files(
    related_type: str = Query(...),
    related_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    files = db.query(FileModel).filter(
        FileModel.related_type == related_type,
        FileModel.related_id == related_id,
        FileModel.is_deleted == False,
    ).order_by(FileModel.uploaded_at.desc()).all()
    return {"data": files, "message": "OK"}


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.is_deleted == False,
    ).first()
    if not file_record:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "ファイルが見つかりません"},
        )

    if not os.path.exists(file_record.stored_path):
        raise HTTPException(
            status_code=404,
            detail={"code": "FILE_MISSING", "message": "ファイルがディスク上に見つかりません"},
        )

    return FileResponse(
        path=file_record.stored_path,
        filename=file_record.original_filename,
        media_type="application/octet-stream",
    )


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.is_deleted == False,
    ).first()
    if not file_record:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "ファイルが見つかりません"},
        )

    file_record.is_deleted = True

    log_audit(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        target_table="t_file",
        target_id=file_record.id,
        changed_fields=["is_deleted"],
        before_value={"is_deleted": False},
        after_value={"is_deleted": True},
    )

    db.commit()
    return {"data": None, "message": "ファイルを削除しました"}
