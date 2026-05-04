"""Inventory API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import InventoryBatch
from app.models.product import Product
from app.models.user import User
from app.schemas.inventory import (
    InventoryBatchListResponse,
    InventoryBatchResponse,
    InventorySummaryResponse,
    InventorySummaryItem,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/batches", response_model=InventoryBatchListResponse)
def list_batches(
    status: str | None = Query("active", description="active yoki finished"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Ombordagi partiyalar (batch) ro'yxati."""
    query = db.query(InventoryBatch)
    if status:
        query = query.filter(InventoryBatch.status == status)
        
    # Active batches first, then newest
    query = query.order_by(
        InventoryBatch.status.asc(), 
        InventoryBatch.id.desc()
    )
    
    items = query.all()
    return InventoryBatchListResponse(
        items=[InventoryBatchResponse.model_validate(b) for b in items],
        total=len(items)
    )


@router.get("/summary", response_model=InventorySummaryResponse)
def get_inventory_summary(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Ombordagi jami qoldiqlar mahsulotlar bo'yicha."""
    # Group by product
    results = (
        db.query(
            InventoryBatch.product_id,
            func.sum(InventoryBatch.remaining_quantity_liters).label("total_qty"),
            func.sum(
                InventoryBatch.remaining_quantity_liters * InventoryBatch.purchase_price_per_liter
            ).label("total_cost")
        )
        .filter(InventoryBatch.status == "active")
        .group_by(InventoryBatch.product_id)
        .all()
    )
    
    # We also want to include the product name, so we fetch products
    products = {p.id: p.name for p in db.query(Product).all()}
    
    items = []
    for row in results:
        qty = row.total_qty or 0
        cost = row.total_cost or 0
        avg_price = cost / qty if qty > 0 else 0
        
        items.append(InventorySummaryItem(
            product_id=row.product_id,
            product_name=products.get(row.product_id, "Noma'lum"),
            total_quantity_liters=qty,
            total_cost=cost,
            average_price_per_liter=avg_price
        ))
        
    return InventorySummaryResponse(
        items=items,
        total_products=len(items)
    )
