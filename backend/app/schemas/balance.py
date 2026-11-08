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
            raise ValueError("Сумма 0 дан кам бўлмаслиги керак")
        return v


class AddInitialBalanceRequest(BaseModel):
    payment_type: PaymentType
    amount: float
    date: str
    note: str = ""

    @field_validator("amount")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Сумма 0 дан катта бўлиши керак")
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
            raise ValueError("Фақат нақд ёки перечисления усули мавжуд")
        return v
