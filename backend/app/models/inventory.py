"""Inventory batch model — tracks fuel stock by batch."""

from datetime import datetime

from sqlalchemy import Integer, Float, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("partners.id"), nullable=False
    )
    purchase_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchases.id"), nullable=False
    )
    purchase_price_per_liter: Mapped[float] = mapped_column(Float, nullable=False)
    initial_quantity_liters: Mapped[float] = mapped_column(Float, nullable=False)
    remaining_quantity_liters: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active | finished
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    product = relationship("Product", lazy="joined")
    supplier = relationship("Partner", lazy="joined")
