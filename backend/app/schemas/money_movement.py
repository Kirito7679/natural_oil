"""Pydantic schemas for money movements."""

from datetime import datetime
from pydantic import BaseModel

from app.utils.enums import PaymentType, MovementType, MovementDirection


class MoneyMovementResponse(BaseModel):
    id: int
    date: datetime
    movement_type: str
    payment_type: str
    direction: str
    amount: float
    related_table: str | None = None
    related_id: int | None = None
    note: str | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MoneyMovementListResponse(BaseModel):
    items: list[MoneyMovementResponse]
    total: int
