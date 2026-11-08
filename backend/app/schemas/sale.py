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
            raise ValueError("Тўлов суммаси 0 дан катта бўлиши керак")
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
            raise ValueError("Миқдор 0 дан катта бўлиши керак")
            
        if self.sale_price_per_liter <= 0:
            raise ValueError("Сотиш нархи 0 дан катта бўлиши керак")

        total_sale = self.quantity_liters * self.sale_price_per_liter
        total_paid = sum(p.amount for p in self.payments)

        if total_paid > total_sale + 0.01:
            raise ValueError("Тўланган сумма умумий сотув суммасидан катта бўлиши мумкин эмас.")

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
