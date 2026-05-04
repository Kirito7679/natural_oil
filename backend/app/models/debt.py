"""Debt models — CustomerDebt, SupplierDebt, and DebtPayment."""

from datetime import datetime

from sqlalchemy import Integer, Float, String, Text, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CustomerDebt(Base):
    __tablename__ = "customer_debts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partners.id"), nullable=False
    )
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales.id"), nullable=False
    )
    original_amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    remaining_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active | closed | cancelled
    last_payment_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    customer = relationship("Partner", lazy="joined")
    sale = relationship("Sale", lazy="joined")


class SupplierDebt(Base):
    __tablename__ = "supplier_debts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partners.id"), nullable=False
    )
    purchase_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchases.id"), nullable=False
    )
    original_amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    remaining_amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active | closed | cancelled
    last_payment_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    supplier = relationship("Partner", lazy="joined")
    purchase = relationship("Purchase", lazy="joined")


class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    debt_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # customer_debt | supplier_debt
    debt_id: Mapped[int] = mapped_column(Integer, nullable=False)
    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partners.id"), nullable=False
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
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    partner = relationship("Partner", lazy="joined")
