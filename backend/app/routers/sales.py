"""Sales API router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleResponse, SaleListResponse
from app.services.sale_service import create_sale, cancel_sale
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.get("", response_model=SaleListResponse)
def list_sales(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Barcha sotuvlar ro'yxati."""
    query = db.query(Sale).order_by(Sale.id.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return SaleListResponse(
        items=[SaleResponse.model_validate(p) for p in items],
        total=total,
    )


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Bitta sotuv haqida ma'lumot."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sotuv topilmadi")
    return SaleResponse.model_validate(sale)


@router.post("", response_model=SaleResponse, status_code=201)
def api_create_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Yangi sotuv yaratish."""
    try:
        sale = create_sale(db, data, user_id=current_user.id)
        return SaleResponse.model_validate(sale)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{sale_id}/cancel", response_model=SaleResponse)
def api_cancel_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sotuvni bekor qilish."""
    try:
        sale = cancel_sale(db, sale_id, user_id=current_user.id)
        return SaleResponse.model_validate(sale)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
