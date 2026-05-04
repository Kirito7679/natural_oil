"""Sale and SalePayment models.

Sales support split payments: one sale can have multiple payment rows
(cash and/or bank_transfer). paid_amount on the sale is the sum of all
payment rows. There is NO card payment type.
"""

from datetime import datetime

from sqlalchemy import Integer, Float, String, Text, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partners.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    inventory_batch_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_batches.id"), nullable=False
    )
    quantity_liters: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price_per_liter: Mapped[float] = mapped_column(Float, nullable=False)
    sale_price_per_liter: Mapped[float] = mapped_column(Float, nullable=False)
    profit_per_liter: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_sale_amount: Mapped[float] = mapped_column(Float, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    debt_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active | cancelled
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    customer = relationship("Partner", lazy="joined")
    product = relationship("Product", lazy="joined")
    inventory_batch = relationship("InventoryBatch", lazy="joined")
    payments = relationship("SalePayment", back_populates="sale", lazy="joined")


class SalePayment(Base):
    """Individual payment row for a sale. Supports split payments."""
    __tablename__ = "sale_payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales.id"), nullable=False
    )
    payment_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # cash | bank_transfer — NO card
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )

    # Relationships
    sale = relationship("Sale", back_populates="payments")
