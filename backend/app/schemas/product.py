"""Pydantic schemas for products."""

from datetime import datetime
from pydantic import BaseModel, field_validator


class ProductCreate(BaseModel):
    name: str
    unit: str = "liter"
    note: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Mahsulot nomi bo'sh bo'lmasligi kerak")
        return v


class ProductUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    note: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Mahsulot nomi bo'sh bo'lmasligi kerak")
        return v


class ProductResponse(BaseModel):
    id: int
    name: str
    unit: str
    is_active: bool
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
