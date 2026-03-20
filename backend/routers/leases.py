import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, require_role
from audit import log_audit
from models.user import User
from models.property import Property
from models.lease import Lease
from models.fee_detail import FeeDetail
from schemas.lease import (
    LeaseCreate, LeaseUpdate, LeaseResponse,
    LeaseListItem, LeaseHistoryResponse,
    LeaseStatusChangeRequest, LeaseRenewalRequest,
)
from schemas.fee import BulkFeeUpdateRequest
from services.lease_service import (
    create_lease, update_lease, delete_lease,
    list_leases, get_lease_history,
    change_status, start_renewal,
)
from services.fee_calculator import calculate_fee

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


@router.post("/bulk-preview")
def bulk_fee_preview(
    body: BulkFeeUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一括料金更新のプレビュー（管理者のみ）"""
    require_role(current_user, ["admin"])

    leases = db.query(Lease).filter(
        Lease.id.in_(body.lease_ids),
        Lease.is_deleted == False,
    ).all()

    if len(leases) != len(body.lease_ids):
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "一部の貸付案件が見つかりません",
        })

    non_active = [l for l in leases if l.status != "active"]
    if non_active:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_STATUS",
            "message": f"アクティブでない案件が含まれています（ID: {[l.id for l in non_active]}）",
        })

    items = []
    for lease in leases:
        prop = db.query(Property).filter(Property.id == lease.property_id).first()
        area_sqm = float(prop.area_sqm) if prop and prop.area_sqm else 0.0
        fee = calculate_fee(
            unit_price=body.new_unit_price,
            area_sqm=area_sqm,
            start_date=lease.start_date,
            end_date=lease.end_date,
            discount_rate=body.discount_rate,
            tax_rate=body.tax_rate,
        )
        items.append({
            "lease_id": lease.id,
            "lease_number": lease.lease_number,
            "lessee_name": lease.lessee_name,
            "property_name": prop.name if prop else None,
            "current_annual_rent": lease.annual_rent,
            "new_total_amount": fee["total_amount"],
        })

    return {"data": {"items": items}, "message": "OK"}


@router.post("/bulk-update-fee")
def bulk_fee_update(
    body: BulkFeeUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一括料金更新（管理者のみ）"""
    require_role(current_user, ["admin"])

    if len(body.lease_ids) > 100:
        raise HTTPException(status_code=400, detail={
            "code": "TOO_MANY_LEASES",
            "message": "一度に更新できるのは100件までです",
        })

    leases = db.query(Lease).filter(
        Lease.id.in_(body.lease_ids),
        Lease.is_deleted == False,
    ).all()

    if len(leases) != len(body.lease_ids):
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "一部の貸付案件が見つかりません",
        })

    non_active = [l for l in leases if l.status != "active"]
    if non_active:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_STATUS",
            "message": f"アクティブでない案件が含まれています（ID: {[l.id for l in non_active]}）",
        })

    ip_address = request.client.host if request.client else None
    updated_count = 0

    try:
        for lease in leases:
            prop = db.query(Property).filter(Property.id == lease.property_id).first()
            area_sqm = float(prop.area_sqm) if prop and prop.area_sqm else 0.0

            # 古いFeeDetailのis_latestをFalseにする
            old_fees = db.query(FeeDetail).filter(
                FeeDetail.case_id == lease.id,
                FeeDetail.case_type == "lease",
                FeeDetail.is_latest == True,
            ).all()
            for old_fee in old_fees:
                old_fee.is_latest = False

            # 新しい料金を計算
            fee = calculate_fee(
                unit_price=body.new_unit_price,
                area_sqm=area_sqm,
                start_date=lease.start_date,
                end_date=lease.end_date,
                discount_rate=body.discount_rate,
                tax_rate=body.tax_rate,
            )

            # 新しいFeeDetailを作成
            new_fee = FeeDetail(
                case_id=lease.id,
                case_type="lease",
                is_latest=True,
                unit_price=fee["unit_price"],
                area_sqm=fee["area_sqm"],
                start_date=lease.start_date,
                end_date=lease.end_date,
                months=fee["months"],
                fraction_days=fee["fraction_days"],
                base_amount=fee["base_amount"],
                fraction_amount=fee["fraction_amount"],
                subtotal=fee["subtotal"],
                discount_rate=fee["discount_rate"],
                discount_reason=body.discount_reason,
                discounted_amount=fee["discounted_amount"],
                tax_rate=fee["tax_rate"],
                tax_amount=fee["tax_amount"],
                total_amount=fee["total_amount"],
                calculated_by=current_user.id,
                formula_version=fee["formula_version"],
            )
            db.add(new_fee)

            # 貸付の年間賃貸料を更新
            old_annual_rent = lease.annual_rent
            lease.annual_rent = fee["total_amount"]

            # 監査ログ
            log_audit(
                db=db,
                user_id=current_user.id,
                action="bulk_fee_update",
                target_table="t_lease",
                target_id=lease.id,
                changed_fields=["annual_rent"],
                before_value={"annual_rent": old_annual_rent},
                after_value={"annual_rent": fee["total_amount"]},
                ip_address=ip_address,
            )

            updated_count += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"data": {"updated_count": updated_count}, "message": "一括料金更新が完了しました"}


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
