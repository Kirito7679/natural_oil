"""Pydantic schemas for Customer and Supplier Debts."""

from datetime import datetime, date
from pydantic import BaseModel, field_validator

from app.utils.enums import PaymentType
from app.schemas.partner import PartnerResponse
from app.schemas.product import ProductResponse


# ── Debt Payment schemas ──────────────────────────────────────────────


class DebtPaymentCreate(BaseModel):
    date: date
    amount: float
    payment_type: PaymentType
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak")
        return v


class DebtPaymentResponse(BaseModel):
    id: int
    debt_type: str
    debt_id: int
    partner_id: int
    payment_type: str
    amount: float
    date: date
    note: str | None = None
    status: str
    created_by: int | None = None
    created_at: datetime

    partner: PartnerResponse

    model_config = {"from_attributes": True}


class DebtPaymentListResponse(BaseModel):
    items: list[DebtPaymentResponse]
    total: int


# ── Customer Debt schemas ─────────────────────────────────────────────


class CustomerDebtSaleInfo(BaseModel):
    """Minimal sale info embedded in customer debt response."""
    id: int
    date: date
    quantity_liters: float
    sale_price_per_liter: float
    total_sale_amount: float
    product: ProductResponse

    model_config = {"from_attributes": True}


class CustomerDebtResponse(BaseModel):
    id: int
    customer_id: int
    sale_id: int
    original_amount: float
    paid_amount: float
    remaining_amount: float
    status: str
    last_payment_date: date | None = None
    created_at: datetime

    customer: PartnerResponse
    sale: CustomerDebtSaleInfo

    model_config = {"from_attributes": True}


class CustomerDebtListResponse(BaseModel):
    items: list[CustomerDebtResponse]
    total: int


# ── Supplier Debt schemas ─────────────────────────────────────────────


class SupplierDebtPurchaseInfo(BaseModel):
    """Minimal purchase info embedded in supplier debt response."""
    id: int
    date: date
    quantity_liters: float
    purchase_price_per_liter: float
    total_amount: float
    product: ProductResponse

    model_config = {"from_attributes": True}


class SupplierDebtResponse(BaseModel):
    id: int
    supplier_id: int
    purchase_id: int
    original_amount: float
    paid_amount: float
    remaining_amount: float
    status: str
    last_payment_date: date | None = None
    created_at: datetime

    supplier: PartnerResponse
    purchase: SupplierDebtPurchaseInfo

    model_config = {"from_attributes": True}


class SupplierDebtListResponse(BaseModel):
    items: list[SupplierDebtResponse]
    total: int
