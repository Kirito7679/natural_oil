"""Pydantic schemas for partners."""

from datetime import datetime
from pydantic import BaseModel, field_validator

from app.utils.enums import PartnerType


class PartnerCreate(BaseModel):
    name: str
    phone: str | None = None
    company_name: str | None = None
    address: str | None = None
    type: PartnerType = PartnerType.CUSTOMER
    note: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Ҳамкор номи бўш бўлмаслиги керак")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: PartnerType) -> PartnerType:
        if v not in (PartnerType.CUSTOMER, PartnerType.SUPPLIER, PartnerType.BOTH):
            raise ValueError("Ҳамкор тури нотўғри")
        return v


class PartnerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    company_name: str | None = None
    address: str | None = None
    type: PartnerType | None = None
    note: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Ҳамкор номи бўш бўлмаслиги керак")
        return v


class PartnerResponse(BaseModel):
    id: int
    name: str
    phone: str | None = None
    company_name: str | None = None
    address: str | None = None
    type: str
    note: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PartnerListResponse(BaseModel):
    items: list[PartnerResponse]
    total: int
