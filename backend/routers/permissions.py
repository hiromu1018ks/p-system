import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, require_role
from models.user import User
from models.property import Property
from models.permission import Permission
from schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionListItem, PermissionHistoryResponse,
    StatusChangeRequest, RenewalRequest,
)
from services.permission_service import (
    create_permission, update_permission, delete_permission,
    list_permissions, get_permission_history,
    change_status, start_renewal,
)

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.get("")
def get_permissions(
    status: str | None = Query(None, description="ステータスフィルタ"),
    q: str | None = Query(None, description="検索キーワード"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = list_permissions(db, q=q, status=status, page=page, per_page=per_page)
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return {
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
        "message": "OK",
    }


@router.post("", status_code=201)
def post_permission(
    body: PermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 対象財産の存在チェック + is_deleted チェック
    prop = db.query(Property).filter(
        Property.id == body.property_id,
        Property.is_deleted == False,
    ).first()
    if not prop:
        raise HTTPException(status_code=404, detail={
            "code": "PROPERTY_NOT_FOUND", "message": "対象財産が見つかりません",
        })

    perm = create_permission(
        db=db,
        data=body.model_dump(),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": perm, "message": "使用許可案件を登録しました"}


@router.get("/{permission_id}")
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    ).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })
    return {"data": perm, "message": "OK"}


@router.put("/{permission_id}")
def put_permission(
    permission_id: int,
    body: PermissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    ).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })

    perm = update_permission(
        db=db, perm=perm,
        data=body.model_dump(exclude_unset=True),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": perm, "message": "使用許可案件を更新しました"}


@router.delete("/{permission_id}")
def delete_permission_endpoint(
    permission_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ["admin"])

    perm = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    ).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })

    perm = delete_permission(
        db=db, perm=perm,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": None, "message": "使用許可案件を削除しました"}


@router.get("/{permission_id}/history")
def get_history(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(Permission).filter(Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })

    history = get_permission_history(db, permission_id)
    return {"data": history, "message": "OK"}


@router.post("/{permission_id}/status")
def post_status_change(
    permission_id: int,
    body: StatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    ).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })

    # approved / issued への遷移は管理者のみ
    if body.new_status in ("approved", "issued"):
        require_role(current_user, ["admin"])
    if body.new_status in ("rejected", "cancelled"):
        require_role(current_user, ["admin"])

    perm = change_status(
        db=db, perm=perm,
        new_status=body.new_status,
        user_id=current_user.id,
        reason=body.reason,
        expected_current_status=body.expected_current_status,
        expected_updated_at=body.expected_updated_at,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": perm, "message": "ステータスを変更しました"}


@router.post("/{permission_id}/renewal")
def post_renewal(
    permission_id: int,
    body: RenewalRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(Permission).filter(
        Permission.id == permission_id,
        Permission.is_deleted == False,
    ).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })

    new_perm = start_renewal(
        db=db, perm=perm,
        user_id=current_user.id,
        reason=body.reason,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": new_perm, "message": "更新手続きを開始しました", "status_code": 201}
