import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, require_role
from models.user import User
from models.property import Property
from models.lease import Lease
from schemas.lease import (
    LeaseCreate, LeaseUpdate, LeaseResponse,
    LeaseListItem, LeaseHistoryResponse,
    LeaseStatusChangeRequest, LeaseRenewalRequest,
)
from services.lease_service import (
    create_lease, update_lease, delete_lease,
    list_leases, get_lease_history,
    change_status, start_renewal,
)

router = APIRouter(prefix="/api/leases", tags=["leases"])


@router.get("")
def get_leases(
    status: str | None = Query(None, description="ステータスフィルタ"),
    q: str | None = Query(None, description="検索キーワード"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = list_leases(db, q=q, status=status, page=page, per_page=per_page)
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
def post_lease(
    body: LeaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(
        Property.id == body.property_id,
        Property.is_deleted == False,
    ).first()
    if not prop:
        raise HTTPException(status_code=404, detail={
            "code": "PROPERTY_NOT_FOUND", "message": "対象財産が見つかりません",
        })

    lease = create_lease(
        db=db,
        data=body.model_dump(),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": lease, "message": "貸付案件を登録しました"}


@router.get("/{lease_id}")
def get_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(
        Lease.id == lease_id,
        Lease.is_deleted == False,
    ).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })
    return {"data": lease, "message": "OK"}


@router.put("/{lease_id}")
def put_lease(
    lease_id: int,
    body: LeaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(
        Lease.id == lease_id,
        Lease.is_deleted == False,
    ).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    lease = update_lease(
        db=db, lease=lease,
        data=body.model_dump(exclude_unset=True),
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": lease, "message": "貸付案件を更新しました"}


@router.delete("/{lease_id}")
def delete_lease_endpoint(
    lease_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ["admin"])

    lease = db.query(Lease).filter(
        Lease.id == lease_id,
        Lease.is_deleted == False,
    ).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    lease = delete_lease(
        db=db, lease=lease,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": None, "message": "貸付案件を削除しました"}


@router.get("/{lease_id}/history")
def get_history(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    history = get_lease_history(db, lease_id)
    return {"data": history, "message": "OK"}


@router.post("/{lease_id}/status")
def post_status_change(
    lease_id: int,
    body: LeaseStatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(
        Lease.id == lease_id,
        Lease.is_deleted == False,
    ).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    # active / expired / terminated への遷移は管理者のみ
    if body.new_status in ("active", "expired", "terminated"):
        require_role(current_user, ["admin"])

    lease = change_status(
        db=db, lease=lease,
        new_status=body.new_status,
        user_id=current_user.id,
        reason=body.reason,
        expected_current_status=body.expected_current_status,
        expected_updated_at=body.expected_updated_at,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": lease, "message": "ステータスを変更しました"}


@router.post("/{lease_id}/renewal")
def post_renewal(
    lease_id: int,
    body: LeaseRenewalRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(
        Lease.id == lease_id,
        Lease.is_deleted == False,
    ).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    new_lease = start_renewal(
        db=db, lease=lease,
        user_id=current_user.id,
        reason=body.reason,
        ip_address=request.client.host if request.client else None,
    )
    return {"data": new_lease, "message": "更新手続きを開始しました", "status_code": 201}
