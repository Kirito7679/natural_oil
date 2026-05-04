"""Pydantic schemas for Expenses and ExpenseCategories."""
from datetime import datetime, date
from pydantic import BaseModel, field_validator
from app.utils.enums import PaymentType


# ── Category schemas ────────────────────────────────────────────────────────

class ExpenseCategoryCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Kategoriya nomi bo'sh bo'lishi mumkin emas")
        return v


class ExpenseCategoryUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class ExpenseCategoryResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Expense schemas ─────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    date: date
    category_id: int
    amount: float
    payment_type: PaymentType
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Summa 0 dan katta bo'lishi kerak.")
        return v


class ExpenseResponse(BaseModel):
    id: int
    date: date
    category_id: int
    amount: float
    payment_type: str
    note: str | None = None
    status: str
    created_by: int | None = None
    created_at: datetime
    category: ExpenseCategoryResponse

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int