"""Pydantic schemas for inventory."""

from datetime import datetime
from pydantic import BaseModel

from app.schemas.product import ProductResponse
from app.schemas.partner import PartnerResponse


class InventoryBatchResponse(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    purchase_id: int
    purchase_price_per_liter: float
    initial_quantity_liters: float
    remaining_quantity_liters: float
    status: str
    created_at: datetime
    
    product: ProductResponse
    supplier: PartnerResponse

    model_config = {"from_attributes": True}


class InventoryBatchListResponse(BaseModel):
    items: list[InventoryBatchResponse]
    total: int


class InventorySummaryItem(BaseModel):
    product_id: int
    product_name: str
    total_quantity_liters: float
    total_cost: float
    average_price_per_liter: float

class InventorySummaryResponse(BaseModel):
    items: list[InventorySummaryItem]
    total_products: int
