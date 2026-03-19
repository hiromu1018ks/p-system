from datetime import date, datetime

from pydantic import BaseModel, field_validator


class FeeCalculateRequest(BaseModel):
    case_id: int
    case_type: str  # "permission" / "lease"
    unit_price: int  # 円/㎡/月
    area_sqm: float
    start_date: date
    end_date: date
    discount_rate: float = 0.0
    discount_reason: str | None = None
    tax_rate: float = 0.10

    @field_validator("case_type")
    @classmethod
    def validate_case_type(cls, v):
        if v not in ("permission", "lease"):
            raise ValueError("case_type は 'permission' または 'lease' である必要があります")
        return v

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price(cls, v):
        if v <= 0:
            raise ValueError("単価は正の数である必要があります")
        return v

    @field_validator("area_sqm")
    @classmethod
    def validate_area(cls, v):
        if v <= 0:
            raise ValueError("面積は正の数である必要があります")
        return v

    @field_validator("discount_rate")
    @classmethod
    def validate_discount(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("減額率は0.0〜1.0の範囲である必要があります")
        return v

    @field_validator("tax_rate")
    @classmethod
    def validate_tax(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("税率は0.0〜1.0の範囲である必要があります")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("終了日は開始日より後である必要があります")
        return v


class FeeDetailResponse(BaseModel):
    id: int
    case_id: int
    case_type: str
    is_latest: bool
    unit_price: int
    area_sqm: float
    start_date: date
    end_date: date
    months: int
    fraction_days: int
    base_amount: int
    fraction_amount: int
    subtotal: int
    discount_rate: float
    discount_reason: str | None
    discounted_amount: int
    tax_rate: float
    tax_amount: int
    total_amount: int
    calculated_at: datetime | None
    calculated_by: int
    formula_version: str

    model_config = {"from_attributes": True}


class UnitPriceCreate(BaseModel):
    property_type: str  # administrative / general
    usage: str
    unit_price: int  # 円/㎡/月
    start_date: date

    @field_validator("property_type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("administrative", "general"):
            raise ValueError("property_type は 'administrative' または 'general' である必要があります")
        return v

    @field_validator("unit_price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("単価は正の数である必要があります")
        return v


class UnitPriceUpdate(BaseModel):
    unit_price: int | None = None
    usage: str | None = None
    end_date: date | None = None


class UnitPriceResponse(BaseModel):
    id: int
    property_type: str
    usage: str
    unit_price: int
    start_date: date
    end_date: date | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
