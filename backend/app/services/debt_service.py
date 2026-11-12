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


def _recalc_last_payment_date(db: Session, debt, debt_type: str) -> None:
    """Bekor qilingandan keyin oxirgi to'lov sanasini qayta hisoblaydi."""
    last = (
        db.query(DebtPayment)
        .filter(
            DebtPayment.debt_type == debt_type,
            DebtPayment.debt_id == debt.id,
            DebtPayment.status == "active",
        )
        .order_by(DebtPayment.date.desc(), DebtPayment.id.desc())
        .first()
    )
    debt.last_payment_date = last.date if last else None


def cancel_debt_payment(
    db: Session, payment_id: int, user_id: int | None = None
) -> DebtPayment:
    """Qarz to'lovini bekor qiladi va hammasini oldingi holatiga qaytaradi.

    Qarzning qolgan summasi tiklanadi, yopilgan qarz yana ochiladi, puli
    balansdan teskari yo'nalishda qaytariladi (mijoz to'lovi — chiqim,
    yetkazib beruvchiga to'lov — kirim).
    """
    payment = db.query(DebtPayment).filter(DebtPayment.id == payment_id).first()
    if not payment:
        raise ValueError("Тўлов топилмади")
    if payment.status != "active":
        raise ValueError("Бу тўлов аллақачон бекор қилинган")

    is_customer = payment.debt_type == DebtType.CUSTOMER_DEBT.value
    model = CustomerDebt if is_customer else SupplierDebt
    debt = db.query(model).filter(model.id == payment.debt_id).first()
    if not debt:
        raise ValueError("Қарз топилмади")

    # 1. To'lovni bekor qilamiz — keyingi hisoblar undan tashqarida bo'lsin
    payment.status = "cancelled"
    db.flush()

    # 2. Qarz summalarini tiklaymiz
    debt.paid_amount -= payment.amount
    if debt.paid_amount < 0.01:
        debt.paid_amount = 0.0
    debt.remaining_amount += payment.amount
    # Yopilgan qarz yana ochiladi. Bekor qilingan qarzga tegmaymiz.
    if debt.status == "closed":
        debt.status = "active"
    _recalc_last_payment_date(db, debt, payment.debt_type)

    # 3. Pulni teskari yo'nalishda qaytaramiz
    update_balance(
        db=db,
        payment_type=PaymentType(payment.payment_type),
        amount=payment.amount,
        direction=MovementDirection.OUTGOING if is_customer else MovementDirection.INCOME,
        movement_type=MovementType.CANCELLATION,
        related_table="debt_payments",
        related_id=payment.id,
        note=f"Қарз тўлови бекор қилинди. Тўлов ID: {payment.id}, Қарз ID: {debt.id}",
        user_id=user_id,
        auto_commit=False,
        on_date=payment.date,
    )

    db.commit()
    db.refresh(payment)
    return payment


def cancel_manual_debt(
    db: Session, debt_type: str, debt_id: int, user_id: int | None = None
):
    """Qo'lda kiritilgan eski qarzni bekor qiladi.

    Sotuv yoki prixodga bog'langan qarz bu yerdan bekor qilinmaydi: uning
    o'rniga o'sha sotuv/prixodning o'zi bekor qilinadi, aks holda ikkisi
    bir-biriga mos kelmay qoladi.
    """
    is_customer = debt_type == DebtType.CUSTOMER_DEBT.value
    model = CustomerDebt if is_customer else SupplierDebt
    debt = db.query(model).filter(model.id == debt_id).first()
    if not debt:
        raise ValueError("Қарз топилмади")
    if debt.status == "cancelled":
        raise ValueError("Бу қарз аллақачон бекор қилинган")

    linked_id = debt.sale_id if is_customer else debt.purchase_id
    if linked_id is not None:
        raise ValueError(
            "Бу қарз сотувдан (приходдан) келиб чиққан. "
            "Уни бекор қилиш учун ўша сотувни (приходни) бекор қилинг."
        )

    active_payments = (
        db.query(DebtPayment)
        .filter(
            DebtPayment.debt_type == debt_type,
            DebtPayment.debt_id == debt.id,
            DebtPayment.status == "active",
        )
        .count()
    )
    if active_payments:
        raise ValueError(
            "Бу қарз бўйича тўлов қилинган. Олдин тўловларни бекор қилинг."
        )

    debt.status = "cancelled"
    debt.remaining_amount = 0.0
    db.commit()
    db.refresh(debt)
    return debt


def partner_net_balances(db: Session) -> list[dict]:
    """Har bir hamkor bo'yicha o'zaro hisob-kitob (vzaimozachyot).

    Bitta odam ham mijoz, ham yetkazib beruvchi bo'lishi mumkin: undan mol
    olamiz va unga sotamiz ham. Ikki qarz alohida ko'rsatilsa, haqiqiy holat
    ko'rinmaydi — shuning uchun bu yerda ular bir-biridan ayiriladi.

    net > 0 — hamkor bizga qarzdor, net < 0 — biz hamkorga qarzdormiz.
    """
    from sqlalchemy import func

    from app.models.partner import Partner

    customer_rows = (
        db.query(CustomerDebt.customer_id, func.sum(CustomerDebt.remaining_amount))
        .filter(CustomerDebt.status == "active")
        .group_by(CustomerDebt.customer_id)
        .all()
    )
    supplier_rows = (
        db.query(SupplierDebt.supplier_id, func.sum(SupplierDebt.remaining_amount))
        .filter(SupplierDebt.status == "active")
        .group_by(SupplierDebt.supplier_id)
        .all()
    )

    they_owe = {pid: float(total or 0.0) for pid, total in customer_rows}
    we_owe = {pid: float(total or 0.0) for pid, total in supplier_rows}

    partner_ids = set(they_owe) | set(we_owe)
    if not partner_ids:
        return []

    partners = {
        p.id: p for p in db.query(Partner).filter(Partner.id.in_(partner_ids)).all()
    }

    result = []
    for pid in partner_ids:
        partner = partners.get(pid)
        if partner is None:
            continue
        theirs = they_owe.get(pid, 0.0)
        ours = we_owe.get(pid, 0.0)
        result.append({
            "partner_id": pid,
            "partner_name": partner.name,
            "partner_type": partner.type,
            "they_owe_us": theirs,
            "we_owe_them": ours,
            # ikki tomoni ham bor — aynan shular uchun kerak
            "mutual": theirs > 0.01 and ours > 0.01,
            "net": theirs - ours,
        })

    # Avval o'zaro qarzi borlar, keyin summasi kattaroqlari
    result.sort(key=lambda r: (not r["mutual"], -abs(r["net"])))
    return result
