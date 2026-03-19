import json
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.property import Property
from models.property_history import PropertyHistory
from audit import log_audit


def generate_property_code(db: Session) -> str:
    """財産コードを自動採番する (P0001, P0002, ...)

    論理削除済みを含む全財産の最大コードを取得し、+1 する。
    これにより削除済みコードとの重複を防ぐ。
    """
    max_code = db.query(Property.property_code).order_by(Property.property_code.desc()).first()

    if max_code and max_code[0]:
        try:
            seq = int(max_code[0][1:]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1

    return f"P{seq:04d}"


def create_property(db: Session, data: dict, user_id: int, ip_address: str | None = None) -> Property:
    """財産を新規登録する"""
    code = generate_property_code(db)
    prop = Property(property_code=code, **data)
    db.add(prop)
    db.flush()

    # 履歴記録
    snapshot = {
        "property_code": prop.property_code,
        "name": prop.name,
        "property_type": prop.property_type,
        "address": prop.address,
        "lot_number": prop.lot_number,
        "land_category": prop.land_category,
        "area_sqm": str(prop.area_sqm) if prop.area_sqm else None,
        "acquisition_date": str(prop.acquisition_date) if prop.acquisition_date else None,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "remarks": prop.remarks,
    }
    history = PropertyHistory(
        target_id=prop.id,
        operation_type="CREATE",
        snapshot=json.dumps(snapshot, ensure_ascii=False),
        changed_by=user_id,
        reason="新規登録",
    )
    db.add(history)

    # 監査ログ
    log_audit(
        db=db,
        user_id=user_id,
        action="CREATE",
        target_table="m_property",
        target_id=prop.id,
        changed_fields=list(data.keys()),
        after_value=snapshot,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(prop)
    return prop


def update_property(db: Session, prop: Property, data: dict, user_id: int, ip_address: str | None = None, reason: str | None = None) -> Property:
    """財産を更新する"""
    before = {
        "name": prop.name,
        "property_type": prop.property_type,
        "address": prop.address,
        "lot_number": prop.lot_number,
        "land_category": prop.land_category,
        "area_sqm": str(prop.area_sqm) if prop.area_sqm else None,
        "acquisition_date": str(prop.acquisition_date) if prop.acquisition_date else None,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "remarks": prop.remarks,
    }

    changed_fields = []
    for key, value in data.items():
        if value is not None and getattr(prop, key, None) != value:
            changed_fields.append(key)
            setattr(prop, key, value)

    if not changed_fields:
        return prop

    db.flush()

    after = {
        "property_code": prop.property_code,
        "name": prop.name,
        "property_type": prop.property_type,
        "address": prop.address,
        "lot_number": prop.lot_number,
        "land_category": prop.land_category,
        "area_sqm": str(prop.area_sqm) if prop.area_sqm else None,
        "acquisition_date": str(prop.acquisition_date) if prop.acquisition_date else None,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "remarks": prop.remarks,
    }

    # 履歴記録
    history = PropertyHistory(
        target_id=prop.id,
        operation_type="UPDATE",
        snapshot=json.dumps(after, ensure_ascii=False),
        changed_by=user_id,
        reason=reason or "更新",
    )
    db.add(history)

    # 監査ログ
    log_audit(
        db=db,
        user_id=user_id,
        action="UPDATE",
        target_table="m_property",
        target_id=prop.id,
        changed_fields=changed_fields,
        before_value=before,
        after_value=after,
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(prop)
    return prop


def delete_property(db: Session, prop: Property, user_id: int, ip_address: str | None = None, reason: str = "削除") -> Property:
    """財産を論理削除する"""
    before = {
        "property_code": prop.property_code,
        "name": prop.name,
        "property_type": prop.property_type,
        "is_deleted": prop.is_deleted,
    }

    prop.is_deleted = True

    # 履歴記録
    history = PropertyHistory(
        target_id=prop.id,
        operation_type="DELETE",
        snapshot=json.dumps({"property_code": prop.property_code, "is_deleted": True}, ensure_ascii=False),
        changed_by=user_id,
        reason=reason,
    )
    db.add(history)

    # 監査ログ
    log_audit(
        db=db,
        user_id=user_id,
        action="DELETE",
        target_table="m_property",
        target_id=prop.id,
        changed_fields=["is_deleted"],
        before_value=before,
        after_value={"is_deleted": True},
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(prop)
    return prop


def list_properties(db: Session, q: str | None = None, property_type: str | None = None, include_deleted: bool = False, page: int = 1, per_page: int = 20) -> tuple[list[Property], int]:
    """財産一覧を取得する（ページング付き）"""
    query = db.query(Property)

    if not include_deleted:
        query = query.filter(Property.is_deleted == False)

    if q:
        query = query.filter(
            or_(
                Property.name.contains(q),
                Property.address.contains(q),
                Property.property_code.contains(q),
                Property.lot_number.contains(q),
            )
        )

    if property_type:
        query = query.filter(Property.property_type == property_type)

    total = query.count()
    items = query.order_by(Property.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_property_history(db: Session, property_id: int) -> list[PropertyHistory]:
    """財産の変更履歴を取得する"""
    return db.query(PropertyHistory).filter(
        PropertyHistory.target_id == property_id
    ).order_by(PropertyHistory.changed_at.desc()).all()
