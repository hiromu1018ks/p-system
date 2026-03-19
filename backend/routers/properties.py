import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.user import User
from models.property import Property
from services.property_service import (
    create_property,
    update_property,
    delete_property,
    list_properties,
    get_property_history,
)

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("")
def get_properties(
    q: str | None = Query(None, description="検索キーワード"),
    type: str | None = Query(None, description="財産区分フィルタ"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = list_properties(db, q=q, property_type=type, page=page, per_page=per_page)
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
def post_property(
    body: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from schemas.property import PropertyCreate
    try:
        validated = PropertyCreate(**body)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
            })
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "入力内容に誤りがあります",
                    "detail": {"errors": errors},
                }
            },
        )
    prop = create_property(
        db=db,
        data=validated.model_dump(exclude_unset=True),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": prop, "message": "財産を登録しました"}


@router.get("/{property_id}")
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(
        Property.id == property_id,
        Property.is_deleted == False,
    ).first()
    if not prop:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "財産が見つかりません"},
        )
    return {"data": prop, "message": "OK"}


@router.put("/{property_id}")
def put_property(
    property_id: int,
    body: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from schemas.property import PropertyUpdate
    validated = PropertyUpdate(**body)
    prop = db.query(Property).filter(
        Property.id == property_id,
        Property.is_deleted == False,
    ).first()
    if not prop:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "財産が見つかりません"},
        )

    prop = update_property(
        db=db,
        prop=prop,
        data=validated.model_dump(exclude_unset=True),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": prop, "message": "財産を更新しました"}


@router.delete("/{property_id}")
def delete_property_endpoint(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(
        Property.id == property_id,
        Property.is_deleted == False,
    ).first()
    if not prop:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "財産が見つかりません"},
        )

    prop = delete_property(
        db=db,
        prop=prop,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": None, "message": "財産を削除しました"}


@router.get("/{property_id}/history")
def get_history(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "財産が見つかりません"},
        )

    history = get_property_history(db, property_id)
    return {"data": history, "message": "OK"}
