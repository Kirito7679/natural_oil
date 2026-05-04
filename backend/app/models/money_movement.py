"""Money movement model — full audit trail of every financial operation."""

from datetime import datetime

from sqlalchemy import Integer, Float, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MoneyMovement(Base):
    __tablename__ = "money_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    movement_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # initial_balance | purchase_payment | sale_payment | customer_debt_payment
    #   supplier_debt_payment | expense | balance_adjustment | cancellation
    payment_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # cash | bank_transfer — NO card
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # income | outgoing
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    related_table: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
