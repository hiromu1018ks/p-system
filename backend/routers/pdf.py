import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.user import User
from models.permission import Permission
from models.lease import Lease
from models.property import Property
from models.document import Document
from services.pdf_generator import generate_pdf
from audit import log_audit

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

PDF_DIR = "generated_pdfs"

ALLOWED_STATUSES = ["approved", "issued", "active", "expired"]

DOCUMENT_TYPE_LABELS = {
    "permission_certificate": "使用許可証",
    "land_lease_contract": "土地貸付契約書",
    "building_lease_contract": "建物貸付契約書",
    "renewal_notice": "更新通知文",
}


def _build_permission_data(perm: Permission, prop: Property) -> dict:
    return {
        "permission_number": perm.permission_number or "（下書き）",
        "applicant_name": perm.applicant_name,
        "applicant_address": perm.applicant_address,
        "property_name": prop.name if prop else "",
        "property_address": prop.address if prop else "",
        "purpose": perm.purpose,
        "start_date": perm.start_date.isoformat() if perm.start_date else "",
        "end_date": perm.end_date.isoformat() if perm.end_date else "",
        "usage_area_sqm": str(perm.usage_area_sqm) if perm.usage_area_sqm else "",
        "fee_amount": perm.fee_amount,
        "conditions": perm.conditions or "",
        "permission_date": perm.permission_date.isoformat() if perm.permission_date else "",
    }


def _build_lease_data(lease: Lease, prop: Property) -> dict:
    return {
        "lease_number": lease.lease_number or "（下書き）",
        "property_name": prop.name if prop else "",
        "property_address": prop.address if prop else "",
        "property_lot_number": prop.lot_number if prop else "",
        "property_area": str(prop.area_sqm) if prop and prop.area_sqm else "",
        "lessee_name": lease.lessee_name,
        "lessee_address": lease.lessee_address,
        "purpose": lease.purpose,
        "start_date": lease.start_date.isoformat() if lease.start_date else "",
        "end_date": lease.end_date.isoformat() if lease.end_date else "",
        "annual_rent": lease.annual_rent,
        "payment_method": lease.payment_method or "",
        "approval_date": date.today().isoformat(),
    }


def _build_renewal_data(case_type: str, case, prop: Property | None) -> dict:
    if case_type == "permission":
        return {
            "case_type": "permission",
            "case_number": case.permission_number or "（下書き）",
            "applicant_name": case.applicant_name,
            "applicant_address": case.applicant_address,
            "purpose": case.purpose,
            "current_end_date": case.end_date.isoformat() if case.end_date else "",
            "new_start_date": "",
            "new_end_date": "",
            "new_fee": case.fee_amount,
            "renewal_deadline": "",
        }
    else:
        return {
            "case_type": "lease",
            "case_number": case.lease_number or "（下書き）",
            "applicant_name": case.lessee_name,
            "applicant_address": case.lessee_address,
            "purpose": case.purpose,
            "current_end_date": case.end_date.isoformat() if case.end_date else "",
            "new_start_date": "",
            "new_end_date": "",
            "new_fee": case.annual_rent,
            "renewal_deadline": "",
        }


def _check_pdf_allowed(case_status: str):
    if case_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=409, detail={
            "code": "INVALID_STATUS_FOR_PDF",
            "message": f"ステータス '{case_status}' の案件はPDF生成できません。許可されるステータス: {', '.join(ALLOWED_STATUSES)}",
        })


def _save_document(db: Session, case_id: int, case_type: str, document_type: str, file_path: str, user_id: int, ip_address: str | None = None):
    doc = Document(
        case_id=case_id,
        case_type=case_type,
        document_type=document_type,
        file_path=file_path,
        generated_by=user_id,
    )
    db.add(doc)

    log_audit(
        db=db, user_id=user_id, action="PDF_GEN",
        target_table="t_document", target_id=doc.id,
        changed_fields=["case_id", "case_type", "document_type"],
        after_value={"case_id": case_id, "document_type": document_type},
        ip_address=ip_address,
    )

    db.commit()
    db.refresh(doc)
    return doc


@router.post("/permission/{permission_id}", status_code=201)
def generate_permission_certificate(
    permission_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    perm = db.query(Permission).filter(Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "使用許可案件が見つかりません",
        })

    _check_pdf_allowed(perm.status)

    prop = db.query(Property).filter(Property.id == perm.property_id).first()
    case_data = _build_permission_data(perm, prop)

    filename = f"許可証_{perm.permission_number or perm.id}.pdf"
    file_path = os.path.join(PDF_DIR, filename)
    generate_pdf("permission_certificate", case_data, file_path)

    doc = _save_document(db, perm.id, "permission", "permission_certificate", file_path, current_user.id, request.client.host if request.client else None)

    return {
        "data": {
            "id": doc.id,
            "document_type": doc.document_type,
            "document_label": DOCUMENT_TYPE_LABELS[doc.document_type],
            "file_path": file_path,
            "filename": filename,
            "download_url": f"/api/pdf/download/{doc.id}",
        },
        "message": "使用許可証を生成しました",
    }


@router.post("/lease-land/{lease_id}", status_code=201)
def generate_land_lease_contract(
    lease_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    _check_pdf_allowed(lease.status)

    prop = db.query(Property).filter(Property.id == lease.property_id).first()
    case_data = _build_lease_data(lease, prop)

    filename = f"土地貸付契約書_{lease.lease_number or lease.id}.pdf"
    file_path = os.path.join(PDF_DIR, filename)
    generate_pdf("land_lease_contract", case_data, file_path)

    doc = _save_document(db, lease.id, "lease", "land_lease_contract", file_path, current_user.id, request.client.host if request.client else None)

    return {
        "data": {
            "id": doc.id,
            "document_type": doc.document_type,
            "document_label": DOCUMENT_TYPE_LABELS[doc.document_type],
            "file_path": file_path,
            "filename": filename,
            "download_url": f"/api/pdf/download/{doc.id}",
        },
        "message": "土地貸付契約書を生成しました",
    }


@router.post("/lease-building/{lease_id}", status_code=201)
def generate_building_lease_contract(
    lease_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "貸付案件が見つかりません",
        })

    if lease.property_sub_type != "building":
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_PROPERTY_TYPE",
            "message": "建物貸付契約書は建物（building）の案件のみ生成できます",
        })

    _check_pdf_allowed(lease.status)

    prop = db.query(Property).filter(Property.id == lease.property_id).first()
    case_data = _build_lease_data(lease, prop)

    filename = f"建物貸付契約書_{lease.lease_number or lease.id}.pdf"
    file_path = os.path.join(PDF_DIR, filename)
    generate_pdf("building_lease_contract", case_data, file_path)

    doc = _save_document(db, lease.id, "lease", "building_lease_contract", file_path, current_user.id, request.client.host if request.client else None)

    return {
        "data": {
            "id": doc.id,
            "document_type": doc.document_type,
            "document_label": DOCUMENT_TYPE_LABELS[doc.document_type],
            "file_path": file_path,
            "filename": filename,
            "download_url": f"/api/pdf/download/{doc.id}",
        },
        "message": "建物貸付契約書を生成しました",
    }


@router.post("/renewal/{case_type}/{case_id}", status_code=201)
def generate_renewal_notice(
    case_type: str,
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if case_type not in ("permission", "lease"):
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_CASE_TYPE", "message": "case_type は 'permission' または 'lease' である必要があります",
        })

    if case_type == "permission":
        case = db.query(Permission).filter(Permission.id == case_id).first()
    else:
        case = db.query(Lease).filter(Lease.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "案件が見つかりません",
        })

    _check_pdf_allowed(case.status)

    prop = db.query(Property).filter(Property.id == case.property_id).first()
    renewal_data = _build_renewal_data(case_type, case, prop)

    label = "使用許可" if case_type == "permission" else "貸付"
    case_num = getattr(case, "permission_number", None) or getattr(case, "lease_number", None) or case_id
    filename = f"更新通知文_{label}_{case_num}.pdf"
    file_path = os.path.join(PDF_DIR, filename)
    generate_pdf("renewal_notice", renewal_data, file_path)

    doc = _save_document(db, case_id, case_type, "renewal_notice", file_path, current_user.id, request.client.host if request.client else None)

    return {
        "data": {
            "id": doc.id,
            "document_type": doc.document_type,
            "document_label": DOCUMENT_TYPE_LABELS[doc.document_type],
            "file_path": file_path,
            "filename": filename,
            "download_url": f"/api/pdf/download/{doc.id}",
        },
        "message": "更新通知文を生成しました",
    }


@router.get("/download/{document_id}")
def download_pdf(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={
            "code": "NOT_FOUND", "message": "PDFドキュメントが見つかりません",
        })

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail={
            "code": "FILE_MISSING", "message": "PDFファイルが見つかりません",
        })

    pdf_abs = os.path.abspath(PDF_DIR)
    file_abs = os.path.abspath(doc.file_path)
    if not file_abs.startswith(pdf_abs):
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_FILE_PATH", "message": "無効なファイルパスです",
        })

    filename = doc.file_path.split("/")[-1]
    return FileResponse(
        path=doc.file_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/history/{case_type}/{case_id}")
def get_document_history(
    case_type: str,
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if case_type not in ("permission", "lease"):
        raise HTTPException(status_code=400, detail={
            "code": "INVALID_CASE_TYPE", "message": "無効な案件種別です",
        })

    docs = db.query(Document).filter(
        Document.case_id == case_id,
        Document.case_type == case_type,
    ).order_by(Document.generated_at.desc()).all()

    return {"data": docs, "message": "OK"}
