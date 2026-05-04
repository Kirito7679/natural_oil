"""Pydantic schemas for balance operations."""

from pydantic import BaseModel, field_validator

from app.utils.enums import PaymentType


class BalanceResponse(BaseModel):
    cash_balance: float
    bank_transfer_balance: float
    total_balance: float


class InitialBalanceRequest(BaseModel):
    cash_amount: float = 0.0
    bank_transfer_amount: float = 0.0

    @field_validator("cash_amount", "bank_transfer_amount")
    @classmethod
    def must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Summa 0 dan kam bo'lmasligi kerak")
        return v


class BalanceAdjustmentRequest(BaseModel):
    payment_type: PaymentType
    amount: float
    note: str = ""

    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, v: PaymentType) -> PaymentType:
        # Extra safety — only cash and bank_transfer allowed
        if v not in (PaymentType.CASH, PaymentType.BANK_TRANSFER):
            raise ValueError("Faqat naqd yoki perechisleniya usuli mavjud")
        return v
