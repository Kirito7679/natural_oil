"""Products router — CRUD endpoints for fuel products."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    active_only: bool = Query(False, description="Faqat faol mahsulotlarni ko'rsatish"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Barcha mahsulotlar ro'yxati."""
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    query = query.order_by(Product.id)
    items = query.all()
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in items],
        total=len(items),
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Bitta mahsulot ma'lumotlari."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Yangi mahsulot qo'shish."""
    # Check duplicate name
    existing = db.query(Product).filter(Product.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"'{data.name}' nomli mahsulot allaqachon mavjud",
        )
    product = Product(
        name=data.name,
        unit=data.unit,
        note=data.note,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Mahsulotni tahrirlash."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")

    if data.name is not None:
        # Check duplicate name (excluding self)
        existing = (
            db.query(Product)
            .filter(Product.name == data.name, Product.id != product_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"'{data.name}' nomli mahsulot allaqachon mavjud",
            )
        product.name = data.name

    if data.unit is not None:
        product.unit = data.unit
    if data.note is not None:
        product.note = data.note
    if data.is_active is not None:
        product.is_active = data.is_active

    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}/toggle", response_model=ProductResponse)
def toggle_product_active(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Mahsulotni faollashtirish yoki o'chirish."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)
