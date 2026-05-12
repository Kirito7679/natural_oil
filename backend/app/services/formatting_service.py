from sqlalchemy.orm import Session
from app.models.money_movement import MoneyMovement
from app.models.sale import Sale
from app.models.purchase import Purchase
from app.models.expense import Expense
from app.models.debt import CustomerDebt, SupplierDebt, DebtPayment

def get_rich_description(db: Session, m: MoneyMovement) -> str:
    """Enrich money movement description based on business rules."""
    note = m.note or ""

    if m.movement_type == "customer_debt_payment":
        partner_name = None

        # Path A: related_table = 'debt_payments' (set by debt_service.pay_customer_debt)
        if m.related_table == "debt_payments" and m.related_id:
            dp = db.query(DebtPayment).filter(DebtPayment.id == m.related_id).first()
            if dp:
                debt = db.query(CustomerDebt).filter(CustomerDebt.id == dp.debt_id).first()
                if debt:
                    partner_name = debt.customer.name if debt.customer else None

        # Path B: related_table = 'customer_debts' (legacy / direct link)
        elif m.related_table == "customer_debts" and m.related_id:
            debt = db.query(CustomerDebt).filter(CustomerDebt.id == m.related_id).first()
            if debt:
                partner_name = debt.customer.name if debt.customer else None

        name = partner_name or "Noma'lum hamkor"
        return f"Mijozdan qarz to'lovi \u2014 {name}"

    elif m.movement_type == "supplier_debt_payment":
        partner_name = None

        # Path A: related_table = 'debt_payments' (set by debt_service.pay_supplier_debt)
        if m.related_table == "debt_payments" and m.related_id:
            dp = db.query(DebtPayment).filter(DebtPayment.id == m.related_id).first()
            if dp:
                debt = db.query(SupplierDebt).filter(SupplierDebt.id == dp.debt_id).first()
                if debt:
                    partner_name = debt.supplier.name if debt.supplier else None

        # Path B: related_table = 'supplier_debts' (legacy / direct link)
        elif m.related_table == "supplier_debts" and m.related_id:
            debt = db.query(SupplierDebt).filter(SupplierDebt.id == m.related_id).first()
            if debt:
                partner_name = debt.supplier.name if debt.supplier else None

        name = partner_name or "Noma'lum hamkor"
        return f"Yetkazib beruvchiga qarz to'lovi \u2014 {name}"

    elif m.movement_type == "sale_payment":
        if m.related_table == "sales" and m.related_id:
            sale = db.query(Sale).filter(Sale.id == m.related_id).first()
            if sale:
                partner_name = sale.customer.name if sale.customer else "Noma'lum hamkor"
                product_name = sale.product.name if sale.product else "Noma'lum mahsulot"
                return f"Sotuv to'lovi — {partner_name} — {product_name}"
        return "Sotuv to'lovi — Noma'lum hamkor"

    elif m.movement_type == "purchase_payment":
        if m.related_table == "purchases" and m.related_id:
            purchase = db.query(Purchase).filter(Purchase.id == m.related_id).first()
            if purchase:
                partner_name = purchase.supplier.name if purchase.supplier else "Noma'lum hamkor"
                product_name = purchase.product.name if purchase.product else "Noma'lum mahsulot"
                return f"Prixod to'lovi — {partner_name} — {product_name}"
        return "Prixod to'lovi — Noma'lum hamkor"

    elif m.movement_type == "expense":
        if m.related_table == "expenses" and m.related_id:
            expense = db.query(Expense).filter(Expense.id == m.related_id).first()
            if expense:
                cat_name = expense.category.name if expense.category else "Boshqa"
                if note:
                    return f"Xarajat — {cat_name} — {note}"
                return f"Xarajat — {cat_name}"
        return f"Xarajat — {note}" if note else "Xarajat"

    elif m.movement_type == "initial_balance":
        payment_type_str = "Naqd" if m.payment_type == "cash" else "Perechisleniya"
        return f"O'zida bor pul qo'shildi — {payment_type_str}"

    elif m.movement_type == "balance_adjustment":
        payment_type_str = "Naqd" if m.payment_type == "cash" else "Perechisleniya"
        if note:
            return f"Balans tuzatildi — {payment_type_str} — {note}"
        return f"Balans tuzatildi — {payment_type_str}"

    return note
