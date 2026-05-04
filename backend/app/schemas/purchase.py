"""Pydantic schemas for purchases."""

from datetime import datetime, date
from pydantic import BaseModel, field_validator, model_validator

from app.utils.enums import PaymentType
from app.schemas.product import ProductResponse
from app.schemas.partner import PartnerResponse


class PurchasePaymentCreate(BaseModel):
    payment_type: PaymentType
    amount: float

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak")
        return v


class PurchaseCreate(BaseModel):
    date: date
    supplier_id: int
    product_id: int
    quantity_liters: float
    
    # User can provide either price per liter OR total amount
    purchase_price_per_liter: float | None = None
    total_amount: float | None = None
    
    payments: list[PurchasePaymentCreate] = []
    note: str | None = None

    @model_validator(mode="after")
    def validate_calculation_inputs(self) -> "PurchaseCreate":
        if self.quantity_liters <= 0:
            raise ValueError("Miqdor 0 dan katta bo'lishi kerak")
            
        if self.purchase_price_per_liter is None and self.total_amount is None:
            raise ValueError("Narx yoki umumiy summa kiritilishi shart")
            
        # Calculate missing fields
        if self.purchase_price_per_liter is not None and self.total_amount is None:
            if self.purchase_price_per_liter <= 0:
                raise ValueError("Narx 0 dan katta bo'lishi kerak")
            self.total_amount = self.quantity_liters * self.purchase_price_per_liter
            
        elif self.total_amount is not None and self.purchase_price_per_liter is None:
            if self.total_amount <= 0:
                raise ValueError("Umumiy summa 0 dan katta bo'lishi kerak")
            self.purchase_price_per_liter = self.total_amount / self.quantity_liters
            
        elif self.purchase_price_per_liter is not None and self.total_amount is not None:
            # Both provided, validate they match (allowing small float rounding differences)
            expected_total = self.quantity_liters * self.purchase_price_per_liter
            if abs(expected_total - self.total_amount) > 0.01:
                raise ValueError("Kiritilgan narx va miqdor bo'yicha summa to'g'ri kelmayapti")
                
        # Validate payments don't exceed total
        total_paid = sum(p.amount for p in self.payments)
        if total_paid > self.total_amount + 0.01:  # small epsilon for floats
            raise ValueError("To'lov summasi umumiy summadan oshmasligi kerak")
            
        return self


class PurchasePaymentResponse(BaseModel):
    id: int
    payment_type: str
    amount: float
    date: date
    status: str

    model_config = {"from_attributes": True}


class PurchaseResponse(BaseModel):
    id: int
    date: date
    supplier_id: int
    product_id: int
    quantity_liters: float
    purchase_price_per_liter: float
    total_amount: float
    paid_amount: float
    debt_amount: float
    note: str | None = None
    status: str
    created_at: datetime
    
    supplier: PartnerResponse
    product: ProductResponse
    payments: list[PurchasePaymentResponse] = []

    model_config = {"from_attributes": True}


class PurchaseListResponse(BaseModel):
    items: list[PurchaseResponse]
    total: int
