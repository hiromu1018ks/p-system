from datetime import date, datetime

from pydantic import BaseModel, field_validator


VALID_LEASE_STATUSES = [
    "draft", "negotiating", "pending_approval",
    "active", "expired", "terminated",
]


class LeaseCreate(BaseModel):
    property_id: int
    property_sub_type: str  # land / building
    lessee_name: str
    lessee_address: str
    lessee_contact: str | None = None
    purpose: str
    start_date: date
    end_date: date
    leased_area: str | None = None
    payment_method: str | None = None  # monthly / semiannual / annual

    @field_validator("property_sub_type")
    @classmethod
    def validate_sub_type(cls, v):
        if v not in ("land", "building"):
            raise ValueError("property_sub_type は 'land' または 'building' である必要があります")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("終了日は開始日より後である必要があります")
        return v

    @field_validator("payment_method")
    @classmethod
    def validate_payment(cls, v):
        if v is not None and v not in ("monthly", "semiannual", "annual"):
            raise ValueError("支払方法は 'monthly' / 'semiannual' / 'annual' である必要があります")
        return v


class LeaseUpdate(BaseModel):
    lessee_name: str | None = None
    lessee_address: str | None = None
    lessee_contact: str | None = None
    purpose: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    leased_area: str | None = None
    override_flag: bool | None = None
    override_reason: str | None = None
    annual_rent: int | None = None
    payment_method: str | None = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment(cls, v):
        if v is not None and v not in ("monthly", "semiannual", "annual"):
            raise ValueError("支払方法は 'monthly' / 'semiannual' / 'annual' である必要があります")
        return v

    @field_validator("override_reason")
    @classmethod
    def validate_override_reason(cls, v, info):
        if info.data.get("override_flag") and not v:
            raise ValueError("手入力上書き時は理由を入力してください")
        return v


class LeaseResponse(BaseModel):
    id: int
    lease_number: str | None
    property_id: int
    parent_case_id: int | None
    renewal_seq: int
    is_latest_case: bool
    property_sub_type: str
    lessee_name: str
    lessee_address: str
    lessee_contact: str | None
    purpose: str
    start_date: date
    end_date: date
    leased_area: str | None
    annual_rent: int | None
    override_flag: bool
    override_reason: str | None
    payment_method: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class LeaseListItem(BaseModel):
    id: int
    lease_number: str | None
    property_id: int
    property_sub_type: str
    lessee_name: str
    purpose: str
    start_date: date
    end_date: date
    annual_rent: int | None
    status: str
    created_at: datetime | None

    model_config = {"from_attributes": True}


class LeaseHistoryResponse(BaseModel):
    id: int
    target_id: int
    operation_type: str
    snapshot: str
    changed_by: int
    changed_at: datetime | None
    reason: str | None

    model_config = {"from_attributes": True}


class LeaseStatusChangeRequest(BaseModel):
    new_status: str
    reason: str
    expected_current_status: str
    expected_updated_at: datetime

    @field_validator("new_status")
    @classmethod
    def validate_new_status(cls, v):
        if v not in VALID_LEASE_STATUSES:
            raise ValueError(f"無効なステータスです: {v}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v, info):
        if info.data.get("new_status") in ("terminated",) and not v:
            raise ValueError("解約時は理由を入力してください")
        return v


class LeaseRenewalRequest(BaseModel):
    reason: str | None = None
