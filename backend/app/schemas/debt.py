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
    sale_id: int | None = None
    original_amount: float
    paid_amount: float
    remaining_amount: float
    status: str
    last_payment_date: date | None = None
    created_at: datetime
    is_manual: bool = False
    manual_date: date | None = None
    manual_product_name: str | None = None
    manual_quantity_liters: float | None = None
    manual_price_per_liter: float | None = None
    manual_note: str | None = None

    customer: PartnerResponse
    sale: CustomerDebtSaleInfo | None = None

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
    purchase_id: int | None = None
    original_amount: float
    paid_amount: float
    remaining_amount: float
    status: str
    last_payment_date: date | None = None
    created_at: datetime
    is_manual: bool = False
    manual_date: date | None = None
    manual_product_name: str | None = None
    manual_quantity_liters: float | None = None
    manual_price_per_liter: float | None = None
    manual_note: str | None = None

    supplier: PartnerResponse
    purchase: SupplierDebtPurchaseInfo | None = None

    model_config = {"from_attributes": True}


class SupplierDebtListResponse(BaseModel):
    items: list[SupplierDebtResponse]
    total: int

class ManualDebtCreate(BaseModel):
    partner_id: int | None = None
    partner_name: str | None = None
    partner_phone: str | None = None
    product_name: str | None = None
    quantity_liters: float | None = None
    price_per_liter: float | None = None
    total_amount: float
    date: date
    note: str | None = None

    @field_validator("total_amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Qarz summasi 0 dan katta bo'lishi kerak")
        return v


# ── Debt Detail (with payment history) ───────────────────────────────────────

class DebtPaymentSimple(BaseModel):
    id: int
    date: date
    amount: float
    payment_type: str
    note: str | None = None

    model_config = {"from_attributes": True}


class CustomerDebtDetail(CustomerDebtResponse):
    """CustomerDebtResponse enriched with payment history."""
    payments: list[DebtPaymentSimple] = []

    model_config = {"from_attributes": True}


class SupplierDebtDetail(SupplierDebtResponse):
    """SupplierDebtResponse enriched with payment history."""
    payments: list[DebtPaymentSimple] = []

    model_config = {"from_attributes": True}
