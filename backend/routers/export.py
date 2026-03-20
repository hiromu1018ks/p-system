import csv
import io

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from audit import log_audit
from models.property import Property
from models.permission import Permission
from models.lease import Lease
from models.user import User

router = APIRouter(prefix="/api/export", tags=["export"])


def _csv_response(filename, rows, headers):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    csv_bytes = output.getvalue().encode("utf-8-sig")  # UTF-8 BOM
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/permissions")
def export_permissions(
    status: str = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        db.query(Permission, Property)
        .outerjoin(Property, Permission.property_id == Property.id)
        .filter(Permission.is_deleted == False)  # noqa: E712
    )
    if status:
        query = query.filter(Permission.status == status)
    results = query.all()

    ip_address = request.client.host if request and request.client else None
    log_audit(
        db,
        user.id,
        "EXPORT",
        "t_permission",
        None,
        changed_fields=["status_filter"],
        before_value=None,
        after_value={"status": status, "count": len(results)},
        ip_address=ip_address,
    )

    headers = [
        "許可番号",
        "財産名称",
        "申請者氏名",
        "申請者住所",
        "使用目的",
        "使用開始日",
        "使用終了日",
        "使用面積(㎡)",
        "使用料(円)",
        "ステータス",
        "許可年月日",
    ]
    rows = []
    for perm, prop in results:
        rows.append(
            [
                perm.permission_number or "",
                prop.name if prop else "",
                perm.applicant_name,
                perm.applicant_address or "",
                perm.purpose or "",
                perm.start_date.isoformat() if perm.start_date else "",
                perm.end_date.isoformat() if perm.end_date else "",
                str(perm.usage_area_sqm) if perm.usage_area_sqm else "",
                str(perm.fee_amount) if perm.fee_amount else "",
                perm.status,
                perm.permission_date.isoformat() if perm.permission_date else "",
            ]
        )
    return _csv_response("permissions.csv", rows, headers)


@router.get("/leases")
def export_leases(
    status: str = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        db.query(Lease, Property)
        .outerjoin(Property, Lease.property_id == Property.id)
        .filter(Lease.is_deleted == False)  # noqa: E712
    )
    if status:
        query = query.filter(Lease.status == status)
    results = query.all()

    ip_address = request.client.host if request and request.client else None
    log_audit(
        db,
        user.id,
        "EXPORT",
        "t_lease",
        None,
        changed_fields=["status_filter"],
        before_value=None,
        after_value={"status": status, "count": len(results)},
        ip_address=ip_address,
    )

    headers = [
        "契約番号",
        "財産名称",
        "財産種別",
        "借受者氏名",
        "借受者住所",
        "貸付目的",
        "契約開始日",
        "契約終了日",
        "貸付面積・部屋番号",
        "年間賃料(円)",
        "支払方法",
        "ステータス",
    ]
    rows = []
    for lease, prop in results:
        rows.append(
            [
                lease.lease_number or "",
                prop.name if prop else "",
                "土地" if lease.property_sub_type == "land" else "建物",
                lease.lessee_name,
                lease.lessee_address or "",
                lease.purpose or "",
                lease.start_date.isoformat() if lease.start_date else "",
                lease.end_date.isoformat() if lease.end_date else "",
                lease.leased_area or "",
                str(lease.annual_rent) if lease.annual_rent else "",
                lease.payment_method or "",
                lease.status,
            ]
        )
    return _csv_response("leases.csv", rows, headers)
