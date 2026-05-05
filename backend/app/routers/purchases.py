"""Purchases API router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.purchase import Purchase
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseResponse, PurchaseListResponse, InitialFuelStockRequest
from app.services.purchase_service import create_purchase, cancel_purchase, create_initial_fuel_stock
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])


@router.get("", response_model=PurchaseListResponse)
def list_purchases(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Barcha prixodlar ro'yxati."""
    query = db.query(Purchase).order_by(Purchase.id.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return PurchaseListResponse(
        items=[PurchaseResponse.model_validate(p) for p in items],
        total=total,
    )


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Bitta prixod haqida ma'lumot."""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Prixod topilmadi")
    return PurchaseResponse.model_validate(purchase)


@router.post("", response_model=PurchaseResponse, status_code=201)
def api_create_purchase(
    data: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Yangi prixod yaratish."""
    try:
        purchase = create_purchase(db, data, user_id=current_user.id)
        return PurchaseResponse.model_validate(purchase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/initial-stock", response_model=PurchaseResponse, status_code=201)
def api_create_initial_fuel_stock(
    data: InitialFuelStockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Boshlang'ich qoldiq (O'zida bor benzin) qo'shish."""
    try:
        purchase = create_initial_fuel_stock(db, data, user_id=current_user.id)
        return PurchaseResponse.model_validate(purchase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{purchase_id}/cancel", response_model=PurchaseResponse)
def api_cancel_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Prixodni bekor qilish."""
    try:
        purchase = cancel_purchase(db, purchase_id, user_id=current_user.id)
        return PurchaseResponse.model_validate(purchase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
