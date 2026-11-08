"""Partners router — CRUD endpoints + stats."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.partner import Partner
from app.models.user import User
from app.models.sale import Sale
from app.models.purchase import Purchase
from app.models.debt import CustomerDebt, SupplierDebt, DebtPayment
from app.schemas.partner import (
    PartnerCreate,
    PartnerUpdate,
    PartnerResponse,
    PartnerListResponse,
)
from app.utils.deps import get_current_user
from app.utils.enums import PartnerType

router = APIRouter(prefix="/api/partners", tags=["Partners"])


@router.get("", response_model=PartnerListResponse)
def list_partners(
    partner_type: str | None = Query(None, description="Turi: customer, supplier, both"),
    active_only: bool = Query(False, description="Фақат фаол ҳамкорлар"),
    search: str | None = Query(None, description="Номи ёки компания номи бўйича қидириш"),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Barcha hamkorlar ro'yxati. Filtrlar: turi, faollik, qidirish."""
    query = db.query(Partner)

    if partner_type:
        if partner_type == "customer":
            query = query.filter(
                Partner.type.in_([PartnerType.CUSTOMER.value, PartnerType.BOTH.value])
            )
        elif partner_type == "supplier":
            query = query.filter(
                Partner.type.in_([PartnerType.SUPPLIER.value, PartnerType.BOTH.value])
            )
        else:
            query = query.filter(Partner.type == partner_type)

    if active_only:
        query = query.filter(Partner.is_active == True)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Partner.name.ilike(search_filter))
            | (Partner.company_name.ilike(search_filter))
            | (Partner.phone.ilike(search_filter))
        )

    query = query.order_by(Partner.id.desc())
    items = query.all()
    return PartnerListResponse(
        items=[PartnerResponse.model_validate(p) for p in items],
        total=len(items),
    )


@router.get("/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Bitta hamkor ma'lumotlari."""
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Ҳамкор топилмади")
    return PartnerResponse.model_validate(partner)


# ── NEW: Partner stats ──────────────────────────────────────────────────────

@router.get("/{partner_id}/stats")
def get_partner_stats(
    partner_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Hamkor statistikasi — sotuv, xarid, qarz, tranzaksiyalar."""

    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Ҳамкор топилмади")

    # === Sales (mijoz bo'lsa — bizdan sotib olgan)
    sales = db.query(Sale).filter(
        Sale.customer_id == partner_id,
        Sale.status == "active",
    ).order_by(Sale.date.desc(), Sale.id.desc()).all()

    total_sale_amount = sum(s.total_sale_amount for s in sales)
    total_sale_qty = sum(s.quantity_liters for s in sales)
    total_sale_count = len(sales)
    last_sale_date = sales[0].date if sales else None

    # === Purchases (yetkazib beruvchi bo'lsa — bizga sotgan)
    purchases = db.query(Purchase).filter(
        Purchase.supplier_id == partner_id,
        Purchase.status == "active",
    ).order_by(Purchase.date.desc(), Purchase.id.desc()).all()

    total_purchase_amount = sum(p.total_amount for p in purchases)
    total_purchase_qty = sum(p.quantity_liters for p in purchases)
    total_purchase_count = len(purchases)
    last_purchase_date = purchases[0].date if purchases else None

    # === Active debts
    customer_debt = db.query(func.sum(CustomerDebt.remaining_amount)).filter(
        CustomerDebt.customer_id == partner_id,
        CustomerDebt.status == "active",
    ).scalar() or 0.0

    supplier_debt = db.query(func.sum(SupplierDebt.remaining_amount)).filter(
        SupplierDebt.supplier_id == partner_id,
        SupplierDebt.status == "active",
    ).scalar() or 0.0

    # === Combined transactions list (sales + purchases + debt payments)
    transactions = []

    for s in sales:
        transactions.append({
            "type": "sale",
            "type_label": "Сотув",
            "id": s.id,
            "date": str(s.date),
            "product": s.product.name if s.product else "",
            "quantity": s.quantity_liters,
            "amount": s.total_sale_amount,
            "paid": s.paid_amount,
            "debt": s.debt_amount,
            "direction": "out",  # Bizdan chiqdi (mijozga)
        })

    for p in purchases:
        transactions.append({
            "type": "purchase",
            "type_label": "Приход",
            "id": p.id,
            "date": str(p.date),
            "product": p.product.name if p.product else "",
            "quantity": p.quantity_liters,
            "amount": p.total_amount,
            "paid": p.paid_amount,
            "debt": p.debt_amount,
            "direction": "in",  # Bizga keldi
        })

    # Debt payments
    debt_payments = db.query(DebtPayment).filter(
        DebtPayment.partner_id == partner_id,
        DebtPayment.status == "active",
    ).order_by(DebtPayment.date.desc(), DebtPayment.id.desc()).all()

    for dp in debt_payments:
        transactions.append({
            "type": "debt_payment",
            "type_label": "Мижоз қарз тўлови" if dp.debt_type == "customer_debt" else "Етказувчи қарз тўлови",
            "id": dp.id,
            "date": str(dp.date),
            "product": "—",
            "quantity": 0,
            "amount": dp.amount,
            "paid": dp.amount,
            "debt": 0,
            "direction": "payment",
            "payment_type": dp.payment_type,
        })

    # Sort by date descending, take last 30
    transactions.sort(key=lambda x: x["date"], reverse=True)
    transactions = transactions[:30]

    return {
        "partner": {
            "id": partner.id,
            "name": partner.name,
            "phone": partner.phone,
            "company_name": partner.company_name,
            "address": partner.address,
            "type": partner.type,
            "is_active": partner.is_active,
        },
        "as_customer": {
            "total_amount": total_sale_amount,
            "total_quantity": total_sale_qty,
            "total_count": total_sale_count,
            "last_date": str(last_sale_date) if last_sale_date else None,
            "active_debt": customer_debt,
        },
        "as_supplier": {
            "total_amount": total_purchase_amount,
            "total_quantity": total_purchase_qty,
            "total_count": total_purchase_count,
            "last_date": str(last_purchase_date) if last_purchase_date else None,
            "active_debt": supplier_debt,
        },
        "transactions": transactions,
    }


@router.post("", response_model=PartnerResponse, status_code=201)
def create_partner(
    data: PartnerCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Yangi hamkor qo'shish."""
    partner = Partner(
        name=data.name,
        phone=data.phone,
        company_name=data.company_name,
        address=data.address,
        type=data.type.value,
        note=data.note,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return PartnerResponse.model_validate(partner)


@router.put("/{partner_id}", response_model=PartnerResponse)
def update_partner(
    partner_id: int,
    data: PartnerUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Hamkorni tahrirlash."""
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Ҳамкор топилмади")

    if data.name is not None:
        partner.name = data.name
    if data.phone is not None:
        partner.phone = data.phone
    if data.company_name is not None:
        partner.company_name = data.company_name
    if data.address is not None:
        partner.address = data.address
    if data.type is not None:
        partner.type = data.type.value
    if data.note is not None:
        partner.note = data.note
    if data.is_active is not None:
        partner.is_active = data.is_active

    db.commit()
    db.refresh(partner)
    return PartnerResponse.model_validate(partner)


@router.patch("/{partner_id}/toggle", response_model=PartnerResponse)
def toggle_partner_active(
    partner_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Hamkorni faollashtirish yoki o'chirish."""
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Ҳамкор топилмади")
    partner.is_active = not partner.is_active
    db.commit()
    db.refresh(partner)
    return PartnerResponse.model_validate(partner)