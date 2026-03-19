from datetime import date, datetime

from pydantic import BaseModel, field_validator


class PropertyCreate(BaseModel):
    name: str
    property_type: str  # administrative / general
    address: str | None = None
    lot_number: str | None = None
    land_category: str | None = None
    area_sqm: float | None = None
    acquisition_date: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    remarks: str | None = None

    @field_validator("property_type")
    @classmethod
    def validate_property_type(cls, v: str) -> str:
        if v not in ("administrative", "general"):
            raise ValueError("property_type は 'administrative' または 'general' である必要があります")
        return v

    @field_validator("land_category")
    @classmethod
    def validate_land_category(cls, v: str | None) -> str | None:
        if v is not None and v not in ("宅地", "田", "畑", "山林", "牧場", "原野", "池沼", "塩田", "鉱泉地", "雑種地", "その他"):
            raise ValueError("無効な地目です")
        return v

    @field_validator("area_sqm")
    @classmethod
    def validate_area_sqm(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("面積は正の数である必要があります")
        return v


class PropertyUpdate(BaseModel):
    name: str | None = None
    property_type: str | None = None
    address: str | None = None
    lot_number: str | None = None
    land_category: str | None = None
    area_sqm: float | None = None
    acquisition_date: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    remarks: str | None = None

    @field_validator("property_type")
    @classmethod
    def validate_property_type(cls, v: str | None) -> str | None:
        if v is not None and v not in ("administrative", "general"):
            raise ValueError("property_type は 'administrative' または 'general' である必要があります")
        return v

    @field_validator("land_category")
    @classmethod
    def validate_land_category(cls, v: str | None) -> str | None:
        if v is not None and v not in ("宅地", "田", "畑", "山林", "牧場", "原野", "池沼", "塩田", "鉱泉地", "雑種地", "その他"):
            raise ValueError("無効な地目です")
        return v

    @field_validator("area_sqm")
    @classmethod
    def validate_area_sqm(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("面積は正の数である必要があります")
        return v


class PropertyResponse(BaseModel):
    id: int
    property_code: str
    name: str
    property_type: str
    address: str | None
    lot_number: str | None
    land_category: str | None
    area_sqm: float | None
    acquisition_date: date | None
    latitude: float | None
    longitude: float | None
    remarks: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class PropertyListItem(BaseModel):
    id: int
    property_code: str
    name: str
    property_type: str
    address: str | None
    land_category: str | None
    area_sqm: float | None
    is_deleted: bool

    model_config = {"from_attributes": True}


class PropertyHistoryResponse(BaseModel):
    id: int
    target_id: int
    operation_type: str
    snapshot: str
    changed_by: int
    changed_at: datetime | None
    reason: str | None

    model_config = {"from_attributes": True}
