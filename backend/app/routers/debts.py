"""Debts API router — customer and supplier debts."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.debt import CustomerDebt, SupplierDebt, DebtPayment
from app.models.user import User
from app.schemas.debt import (
    CustomerDebtListResponse, CustomerDebtResponse,
    SupplierDebtListResponse, SupplierDebtResponse,
    DebtPaymentCreate, DebtPaymentResponse,
)
from app.services.debt_service import pay_customer_debt, pay_supplier_debt
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/debts", tags=["Debts"])


# ── Customer Debts ──────────────────────────────────────────────────────────

@router.get("/customer", response_model=CustomerDebtListResponse)
def list_customer_debts(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Mijozlar qarzdorligi ro'yxati."""
    query = db.query(CustomerDebt).order_by(CustomerDebt.id.desc())
    if status:
        query = query.filter(CustomerDebt.status == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return CustomerDebtListResponse(
        items=[CustomerDebtResponse.model_validate(d) for d in items],
        total=total,
    )


@router.get("/customer/{debt_id}", response_model=CustomerDebtResponse)
def get_customer_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    debt = db.query(CustomerDebt).filter(CustomerDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Qarz topilmadi")
    return CustomerDebtResponse.model_validate(debt)


@router.post("/customer/{debt_id}/pay", response_model=DebtPaymentResponse, status_code=201)
def api_pay_customer_debt(
    debt_id: int,
    data: DebtPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mijoz qarzini to'lash."""
    try:
        payment = pay_customer_debt(db, debt_id, data, user_id=current_user.id)
        return DebtPaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Supplier Debts ──────────────────────────────────────────────────────────

@router.get("/supplier", response_model=SupplierDebtListResponse)
def list_supplier_debts(
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Yetkazib beruvchilarga qarzlar ro'yxati."""
    query = db.query(SupplierDebt).order_by(SupplierDebt.id.desc())
    if status:
        query = query.filter(SupplierDebt.status == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return SupplierDebtListResponse(
        items=[SupplierDebtResponse.model_validate(d) for d in items],
        total=total,
    )


@router.get("/supplier/{debt_id}", response_model=SupplierDebtResponse)
def get_supplier_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    debt = db.query(SupplierDebt).filter(SupplierDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Qarz topilmadi")
    return SupplierDebtResponse.model_validate(debt)


@router.post("/supplier/{debt_id}/pay", response_model=DebtPaymentResponse, status_code=201)
def api_pay_supplier_debt(
    debt_id: int,
    data: DebtPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Yetkazib beruvchi qarzini to'lash."""
    try:
        payment = pay_supplier_debt(db, debt_id, data, user_id=current_user.id)
        return DebtPaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))