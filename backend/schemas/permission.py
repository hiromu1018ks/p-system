from datetime import date, datetime

from pydantic import BaseModel, field_validator


VALID_PERMISSION_STATUSES = [
    "draft", "submitted", "under_review", "pending_approval",
    "approved", "issued", "rejected", "expired", "cancelled",
]


class PermissionCreate(BaseModel):
    property_id: int
    applicant_name: str
    applicant_address: str
    purpose: str
    start_date: date
    end_date: date
    usage_area_sqm: float | None = None
    conditions: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("終了日は開始日より後である必要があります")
        return v

    @field_validator("usage_area_sqm")
    @classmethod
    def validate_area(cls, v):
        if v is not None and v <= 0:
            raise ValueError("面積は正の数である必要があります")
        return v


class PermissionUpdate(BaseModel):
    applicant_name: str | None = None
    applicant_address: str | None = None
    purpose: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    usage_area_sqm: float | None = None
    override_flag: bool | None = None
    override_reason: str | None = None
    fee_amount: int | None = None
    conditions: str | None = None

    @field_validator("usage_area_sqm")
    @classmethod
    def validate_area(cls, v):
        if v is not None and v <= 0:
            raise ValueError("面積は正の数である必要があります")
        return v

    @field_validator("override_reason")
    @classmethod
    def validate_override_reason(cls, v, info):
        if info.data.get("override_flag") and not v:
            raise ValueError("手入力上書き時は理由を入力してください")
        return v


class PermissionResponse(BaseModel):
    id: int
    permission_number: str | None
    property_id: int
    parent_case_id: int | None
    renewal_seq: int
    is_latest_case: bool
    applicant_name: str
    applicant_address: str
    purpose: str
    start_date: date
    end_date: date
    usage_area_sqm: float | None
    fee_amount: int | None
    override_flag: bool
    override_reason: str | None
    conditions: str | None
    status: str
    permission_date: date | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class PermissionListItem(BaseModel):
    id: int
    permission_number: str | None
    property_id: int
    applicant_name: str
    purpose: str
    start_date: date
    end_date: date
    status: str
    fee_amount: int | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class PermissionHistoryResponse(BaseModel):
    id: int
    target_id: int
    operation_type: str
    snapshot: str
    changed_by: int
    changed_at: datetime | None
    reason: str | None

    model_config = {"from_attributes": True}


class StatusChangeRequest(BaseModel):
    new_status: str
    reason: str
    expected_current_status: str
    expected_updated_at: datetime

    @field_validator("new_status")
    @classmethod
    def validate_new_status(cls, v):
        if v not in VALID_PERMISSION_STATUSES:
            raise ValueError(f"無効なステータスです: {v}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v, info):
        # rejected / cancelled は理由必須
        if info.data.get("new_status") in ("rejected", "cancelled") and not v:
            raise ValueError("差戻し・取消時は理由を入力してください")
        return v


class RenewalRequest(BaseModel):
    reason: str | None = None
