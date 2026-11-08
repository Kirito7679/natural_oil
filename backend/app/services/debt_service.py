"""Debt payment business logic — customer and supplier debt payments.

Customer debt payment → increases balance (income).
Supplier debt payment → decreases balance (outgoing).

Only cash and bank_transfer payment types. NO card.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.debt import CustomerDebt, SupplierDebt, DebtPayment
from app.schemas.debt import DebtPaymentCreate
from app.services.balance_service import update_balance
from app.utils.enums import PaymentType, MovementType, MovementDirection, DebtType


def pay_customer_debt(
    db: Session, debt_id: int, data: DebtPaymentCreate, user_id: int | None = None
) -> DebtPayment:
    """Process a customer debt payment — increases balance."""

    debt = db.query(CustomerDebt).filter(CustomerDebt.id == debt_id).first()
    if not debt:
        raise ValueError("Қарз топилмади")
    if debt.status != "active":
        raise ValueError("Бу қарз аллақачон ёпилган.")
    if data.amount > debt.remaining_amount + 0.01:
        raise ValueError("Тўлов суммаси қолган қарздан катта бўлиши мумкин эмас.")

    # 1. Create debt payment record
    payment = DebtPayment(
        debt_type=DebtType.CUSTOMER_DEBT.value,
        debt_id=debt.id,
        partner_id=debt.customer_id,
        payment_type=data.payment_type.value,
        amount=data.amount,
        date=data.date,
        note=data.note,
        created_by=user_id,
    )
    db.add(payment)
    db.flush()

    # 2. Update debt amounts
    debt.paid_amount += data.amount
    debt.remaining_amount -= data.amount
    debt.last_payment_date = data.date

    if debt.remaining_amount <= 0.01:
        debt.remaining_amount = 0.0
        debt.status = "closed"

    # 3. Increase balance (income)
    update_balance(
        db=db,
        payment_type=data.payment_type,
        amount=data.amount,
        direction=MovementDirection.INCOME,
        movement_type=MovementType.CUSTOMER_DEBT_PAYMENT,
        related_table="debt_payments",
        related_id=payment.id,
        note=f"Мижоз қарз тўлови. Қарз ID: {debt.id}, Мижоз: {debt.customer_id}",
        user_id=user_id,
        auto_commit=False,
        on_date=data.date,
    )

    db.commit()
    db.refresh(payment)
    return payment


def pay_supplier_debt(
    db: Session, debt_id: int, data: DebtPaymentCreate, user_id: int | None = None
) -> DebtPayment:
    """Process a supplier debt payment — decreases balance."""

    debt = db.query(SupplierDebt).filter(SupplierDebt.id == debt_id).first()
    if not debt:
        raise ValueError("Қарз топилмади")
    if debt.status != "active":
        raise ValueError("Бу қарз аллақачон ёпилган.")
    if data.amount > debt.remaining_amount + 0.01:
        raise ValueError("Тўлов суммаси қолган қарздан катта бўлиши мумкин эмас.")

    # 1. Create debt payment record
    payment = DebtPayment(
        debt_type=DebtType.SUPPLIER_DEBT.value,
        debt_id=debt.id,
        partner_id=debt.supplier_id,
        payment_type=data.payment_type.value,
        amount=data.amount,
        date=data.date,
        note=data.note,
        created_by=user_id,
    )
    db.add(payment)
    db.flush()

    # 2. Update debt amounts
    debt.paid_amount += data.amount
    debt.remaining_amount -= data.amount
    debt.last_payment_date = data.date

    if debt.remaining_amount <= 0.01:
        debt.remaining_amount = 0.0
        debt.status = "closed"

    # 3. Decrease balance (outgoing) — will raise ValueError if insufficient
    update_balance(
        db=db,
        payment_type=data.payment_type,
        amount=data.amount,
        direction=MovementDirection.OUTGOING,
        movement_type=MovementType.SUPPLIER_DEBT_PAYMENT,
        related_table="debt_payments",
        related_id=payment.id,
        note=f"Етказиб берувчи қарз тўлови. Қарз ID: {debt.id}, Етказиб берувчи: {debt.supplier_id}",
        user_id=user_id,
        auto_commit=False,
        on_date=data.date,
    )

    db.commit()
    db.refresh(payment)
    return payment
