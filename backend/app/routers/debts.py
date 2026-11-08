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
    ManualDebtCreate,
    CustomerDebtDetail, SupplierDebtDetail, DebtPaymentSimple,
)
from app.services.debt_service import pay_customer_debt, pay_supplier_debt
from app.utils.deps import get_current_user
from app.models.partner import Partner

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
        raise HTTPException(status_code=404, detail="Қарз топилмади")
    return CustomerDebtResponse.model_validate(debt)


@router.get("/customer/{debt_id}/detail")
def get_customer_debt_detail(
    debt_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Mijoz qarzi tafsilotlari — to'lovlar tarixi bilan."""
    debt = db.query(CustomerDebt).filter(CustomerDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Қарз топилмади")
    payments = db.query(DebtPayment).filter(
        DebtPayment.debt_type == "customer_debt",
        DebtPayment.debt_id == debt_id,
        DebtPayment.status == "active",
    ).order_by(DebtPayment.date.desc(), DebtPayment.id.desc()).all()
    base = CustomerDebtResponse.model_validate(debt)
    return {
        **base.model_dump(),
        "payments": [
            {"id": p.id, "date": str(p.date), "amount": p.amount,
             "payment_type": p.payment_type, "note": p.note}
            for p in payments
        ]
    }


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


@router.post("/customer/manual", response_model=CustomerDebtResponse, status_code=201)
def api_create_manual_customer_debt(
    data: ManualDebtCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Eski mijoz qarzini qo'shish."""
    if data.partner_id:
        partner = db.query(Partner).filter(
            Partner.id == data.partner_id, 
            Partner.type.in_(["customer", "both"])
        ).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Мижоз топилмади")
    else:
        if not data.partner_name:
            raise HTTPException(status_code=400, detail="Мижоз номи ёки ID'сини киритиш мажбурий")
        partner = Partner(
            name=data.partner_name,
            phone=data.partner_phone,
            type="customer",
        )
        db.add(partner)
        db.flush()

    debt = CustomerDebt(
        customer_id=partner.id,
        sale_id=None,
        original_amount=data.total_amount,
        remaining_amount=data.total_amount,
        paid_amount=0.0,
        status="active",
        is_manual=True,
        manual_date=data.date,
        manual_product_name=data.product_name,
        manual_quantity_liters=data.quantity_liters,
        manual_price_per_liter=data.price_per_liter,
        manual_note=data.note
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return CustomerDebtResponse.model_validate(debt)


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
        raise HTTPException(status_code=404, detail="Қарз топилмади")
    return SupplierDebtResponse.model_validate(debt)


@router.get("/supplier/{debt_id}/detail")
def get_supplier_debt_detail(
    debt_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Yetkazib beruvchi qarzi tafsilotlari — to'lovlar tarixi bilan."""
    debt = db.query(SupplierDebt).filter(SupplierDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Қарз топилмади")
    payments = db.query(DebtPayment).filter(
        DebtPayment.debt_type == "supplier_debt",
        DebtPayment.debt_id == debt_id,
        DebtPayment.status == "active",
    ).order_by(DebtPayment.date.desc(), DebtPayment.id.desc()).all()
    base = SupplierDebtResponse.model_validate(debt)
    return {
        **base.model_dump(),
        "payments": [
            {"id": p.id, "date": str(p.date), "amount": p.amount,
             "payment_type": p.payment_type, "note": p.note}
            for p in payments
        ]
    }


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


@router.post("/supplier/manual", response_model=SupplierDebtResponse, status_code=201)
def api_create_manual_supplier_debt(
    data: ManualDebtCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Eski yetkazib beruvchi qarzini qo'shish."""
    if data.partner_id:
        partner = db.query(Partner).filter(
            Partner.id == data.partner_id, 
            Partner.type.in_(["supplier", "both"])
        ).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Етказиб берувчи топилмади")
    else:
        if not data.partner_name:
            raise HTTPException(status_code=400, detail="Етказиб берувчи номи ёки ID'сини киритиш мажбурий")
        partner = Partner(
            name=data.partner_name,
            phone=data.partner_phone,
            type="supplier",
        )
        db.add(partner)
        db.flush()

    debt = SupplierDebt(
        supplier_id=partner.id,
        purchase_id=None,
        original_amount=data.total_amount,
        remaining_amount=data.total_amount,
        paid_amount=0.0,
        status="active",
        is_manual=True,
        manual_date=data.date,
        manual_product_name=data.product_name,
        manual_quantity_liters=data.quantity_liters,
        manual_price_per_liter=data.price_per_liter,
        manual_note=data.note
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return SupplierDebtResponse.model_validate(debt)