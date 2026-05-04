"""Pydantic schemas for Sales."""

from datetime import datetime, date
from pydantic import BaseModel, field_validator, model_validator

from app.utils.enums import PaymentType
from app.schemas.product import ProductResponse
from app.schemas.partner import PartnerResponse
from app.schemas.inventory import InventoryBatchResponse


class SalePaymentCreate(BaseModel):
    payment_type: PaymentType
    amount: float

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak")
        return v


class SaleCreate(BaseModel):
    date: date
    customer_id: int
    product_id: int
    inventory_batch_id: int
    quantity_liters: float
    sale_price_per_liter: float
    
    # We require the client to pass the purchase_price_per_liter they saw,
    # to ensure consistency during validation.
    purchase_price_per_liter: float
    
    payments: list[SalePaymentCreate] = []
    note: str | None = None

    @model_validator(mode="after")
    def validate_sale(self) -> "SaleCreate":
        if self.quantity_liters <= 0:
            raise ValueError("Miqdor 0 dan katta bo'lishi kerak")
            
        if self.sale_price_per_liter <= 0:
            raise ValueError("Sotish narxi 0 dan katta bo'lishi kerak")

        total_sale = self.quantity_liters * self.sale_price_per_liter
        total_paid = sum(p.amount for p in self.payments)

        if total_paid > total_sale + 0.01:
            raise ValueError("To'langan summa umumiy sotuv summasidan katta bo'lishi mumkin emas.")

        return self


class SalePaymentResponse(BaseModel):
    id: int
    payment_type: str
    amount: float
    date: date
    status: str

    model_config = {"from_attributes": True}


class SaleResponse(BaseModel):
    id: int
    date: date
    customer_id: int
    product_id: int
    inventory_batch_id: int
    quantity_liters: float
    purchase_price_per_liter: float
    sale_price_per_liter: float
    profit_per_liter: float
    total_cost: float
    total_sale_amount: float
    total_profit: float
    paid_amount: float
    debt_amount: float
    note: str | None = None
    status: str
    created_at: datetime
    
    customer: PartnerResponse
    product: ProductResponse
    inventory_batch: InventoryBatchResponse
    payments: list[SalePaymentResponse] = []

    model_config = {"from_attributes": True}


class SaleListResponse(BaseModel):
    items: list[SaleResponse]
    total: int
