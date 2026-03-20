from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, require_role
from models.user import User
from models.permission import Permission
from models.lease import Lease
from models.fee_detail import FeeDetail
from models.unit_price import UnitPrice
from schemas.fee import (
    FeeCalculateRequest, FeeDetailResponse,
    UnitPriceCreate, UnitPriceUpdate, UnitPriceResponse,
)
from services.fee_calculator import calculate_fee
from audit import log_audit

router = APIRouter(tags=["fees"])


def _serialize_dates(obj):
    """date/datetime を文字列に変換して JSON シリアライズ可能にする"""
    if isinstance(obj, dict):
        return {k: _serialize_dates(v) for k, v in obj.items()}
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _orm_to_dict(orm_obj):
    """SQLAlchemy ORM オブジェクトを dict に変換する"""
    result = {}
    for col in orm_obj.__table__.columns:
        val = getattr(orm_obj, col.key)
        if isinstance(val, (date, datetime)):
            val = val.isoformat()
        elif isinstance(val, bytes):
            val = val.decode("utf-8") if val else None
        result[col.key] = val
    return result


@router.post("/api/fees/calculate", status_code=201)
def post_calculate_fee(
    body: FeeCalculateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 案件の存在チェック
    if body.case_type == "permission":
        case = db.query(Permission).filter(Permission.id == body.case_id).first()
    elif body.case_type == "lease":
        case = db.query(Lease).filter(Lease.id == body.case_id).first()
    else:
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_CASE_TYPE", "message": "無効な案件種別です",
        })
    if not case:
        raise HTTPException(status_code=404, detail={
            "code": "CASE_NOT_FOUND", "message": "案件が見つかりません",
        })

    # 計算実行
    result = calculate_fee(
        unit_price=body.unit_price,
        area_sqm=body.area_sqm,
        start_date=body.start_date,
        end_date=body.end_date,
        discount_rate=body.discount_rate,
        tax_rate=body.tax_rate,
    )

    # 旧レコードの is_latest を false に
    db.query(FeeDetail).filter(
        FeeDetail.case_id == body.case_id,
        FeeDetail.case_type == body.case_type,
        FeeDetail.is_latest == True,
    ).update({"is_latest": False})

    # 新レコード保存
    fee = FeeDetail(
        case_id=body.case_id,
        case_type=body.case_type,
        is_latest=True,
        unit_price=result["unit_price"],
        area_sqm=result["area_sqm"],
        start_date=body.start_date,
        end_date=body.end_date,
        months=result["months"],
        fraction_days=result["fraction_days"],
        base_amount=result["base_amount"],
        fraction_amount=result["fraction_amount"],
        subtotal=result["subtotal"],
        discount_rate=result["discount_rate"],
        discount_reason=body.discount_reason,
        discounted_amount=result["discounted_amount"],
        tax_rate=result["tax_rate"],
        tax_amount=result["tax_amount"],
        total_amount=result["total_amount"],
        calculated_by=current_user.id,
        formula_version=result["formula_version"],
    )
    db.add(fee)

    log_audit(
        db=db, user_id=current_user.id, action="CREATE",
        target_table="t_fee_detail", target_id=fee.id,
        changed_fields=["case_id", "total_amount"],
        after_value={"total_amount": fee.total_amount},
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(fee)

    # 案件の fee_amount を更新（override_flag が OFF の場合）
    if body.case_type == "permission" and not case.override_flag:
        case.fee_amount = fee.total_amount
        db.commit()
    elif body.case_type == "lease" and not case.override_flag:
        case.annual_rent = fee.total_amount
        db.commit()

    return {"data": _orm_to_dict(fee), "message": "料金を計算しました"}


@router.get("/api/fees/{case_type}/{case_id}")
def get_fee_details(
    case_type: str,
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if case_type not in ("permission", "lease"):
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_CASE_TYPE", "message": "無効な案件種別です",
        })
    fees = db.query(FeeDetail).filter(
        FeeDetail.case_id == case_id,
        FeeDetail.case_type == case_type,
    ).order_by(FeeDetail.calculated_at.desc()).all()
    return {"data": [_orm_to_dict(f) for f in fees], "message": "OK"}


# --- 単価マスタ ---

@router.get("/api/unit-prices")
def list_unit_prices(
    property_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(UnitPrice)
    if property_type:
        query = query.filter(UnitPrice.property_type == property_type)
    items = query.order_by(UnitPrice.start_date.desc()).all()
    return {"data": [_orm_to_dict(u) for u in items], "message": "OK"}


@router.post("/api/unit-prices", status_code=201)
def create_unit_price(
    body: UnitPriceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    up = UnitPrice(**body.model_dump())
    db.add(up)

    log_audit(
        db=db, user_id=current_user.id, action="CREATE",
        target_table="m_unit_price", target_id=up.id,
        changed_fields=list(body.model_dump().keys()),
        after_value=_serialize_dates(body.model_dump()),
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(up)
    return {"data": _orm_to_dict(up), "message": "単価を登録しました"}


@router.put("/api/unit-prices/{unit_price_id}")
def update_unit_price(
    unit_price_id: int,
    body: UnitPriceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ["admin"])

    up = db.query(UnitPrice).filter(UnitPrice.id == unit_price_id).first()
    if not up:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "単価マスタが見つかりません",
        })

    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(up, key, value)

    log_audit(
        db=db, user_id=current_user.id, action="UPDATE",
        target_table="m_unit_price", target_id=up.id,
        changed_fields=list(body.model_dump(exclude_unset=True).keys()),
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(up)
    return {"data": _orm_to_dict(up), "message": "単価を更新しました"}
