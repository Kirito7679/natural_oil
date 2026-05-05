"""Reports and Dashboard API router."""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.sale import Sale
from app.models.purchase import Purchase
from app.models.expense import Expense
from app.models.debt import CustomerDebt, SupplierDebt
from app.models.money_movement import MoneyMovement
from app.models.balance import BalanceAccount
from app.models.inventory import InventoryBatch
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Dashboard uchun asosiy statistika."""
    today = date.today()

    # Balances
    accounts = db.query(BalanceAccount).all()
    cash_balance = next((a.current_balance for a in accounts if a.type == "cash"), 0.0)
    bank_balance = next((a.current_balance for a in accounts if a.type == "bank_transfer"), 0.0)

    # Today's sales (operational stats)
    today_sales = db.query(Sale).filter(
        Sale.date == today, Sale.status == "active"
    ).all()
    today_profit = sum(s.total_profit for s in today_sales)

    # Today's income money (Bugungi tushum)
    today_movements = db.query(MoneyMovement).filter(
        func.date(MoneyMovement.date) == today,
        MoneyMovement.direction == "income"
    ).all()
    
    # Bugungi tushum includes all actual money in except initial_balance
    today_income_amount = sum(
        m.amount for m in today_movements 
        if m.movement_type != "initial_balance"
    )

    # Today's purchases
    today_purchases = db.query(Purchase).filter(
        Purchase.date == today, Purchase.status == "active"
    ).all()
    today_purchase_amount = sum(p.total_amount for p in today_purchases)

    # Today's expenses
    today_expenses = db.query(Expense).filter(
        Expense.date == today, Expense.status == "active"
    ).all()
    today_expense_amount = sum(e.amount for e in today_expenses)

    # Total active debts
    total_customer_debt = db.query(
        func.sum(CustomerDebt.remaining_amount)
    ).filter(CustomerDebt.status == "active").scalar() or 0.0

    total_supplier_debt = db.query(
        func.sum(SupplierDebt.remaining_amount)
    ).filter(SupplierDebt.status == "active").scalar() or 0.0

    # Total inventory value
    active_batches = db.query(InventoryBatch).filter(InventoryBatch.status == "active").all()
    inventory_value = sum(b.remaining_quantity_liters * b.purchase_price_per_liter for b in active_batches)

    # Recent movements (last 10)
    recent_movements = db.query(MoneyMovement).order_by(
        MoneyMovement.id.desc()
    ).limit(10).all()

    return {
        "balances": {
            "cash": cash_balance,
            "bank_transfer": bank_balance,
            "total": cash_balance + bank_balance,
        },
        "today": {
            "income_amount": today_income_amount,
            "sale_count": len(today_sales),
            "profit": today_profit,
            "purchase_amount": today_purchase_amount,
            "purchase_count": len(today_purchases),
            "expense_amount": today_expense_amount,
            "expense_count": len(today_expenses),
        },
        "debts": {
            "customer_total": total_customer_debt,
            "supplier_total": total_supplier_debt,
        },
        "inventory_value": inventory_value,
        "recent_movements": [
            {
                "id": m.id,
                "date": m.date.isoformat(),
                "movement_type": m.movement_type,
                "payment_type": m.payment_type,
                "direction": m.direction,
                "amount": m.amount,
                "note": m.note,
            }
            for m in recent_movements
        ],
    }


@router.get("/summary")
def get_report(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    payment_type: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Hisobot — sana oralig'i bo'yicha."""

    if not date_from:
        date_from = date.today().replace(day=1)  # Oy boshi
    if not date_to:
        date_to = date.today()

    # Sales
    sale_q = db.query(Sale).filter(
        Sale.date >= date_from,
        Sale.date <= date_to,
        Sale.status == "active",
    )
    sales = sale_q.all()
    total_sale_amount = sum(s.total_sale_amount for s in sales)
    total_profit = sum(s.total_profit for s in sales)
    total_cost = sum(s.total_cost for s in sales)

    # Purchases
    purchase_q = db.query(Purchase).filter(
        Purchase.date >= date_from,
        Purchase.date <= date_to,
        Purchase.status == "active",
    )
    if payment_type:
        purchase_q = purchase_q.filter(Purchase.payment_type == payment_type)
    purchases = purchase_q.all()
    total_purchase_amount = sum(p.total_amount for p in purchases)

    # Expenses
    expense_q = db.query(Expense).filter(
        Expense.date >= date_from,
        Expense.date <= date_to,
        Expense.status == "active",
    )
    if payment_type:
        expense_q = expense_q.filter(Expense.payment_type == payment_type)
    expenses = expense_q.all()
    total_expense_amount = sum(e.amount for e in expenses)

    # Expense breakdown by category
    expense_by_category = {}
    for e in expenses:
        cat_name = e.category.name if e.category else "Boshqa"
        expense_by_category[cat_name] = expense_by_category.get(cat_name, 0) + e.amount

    # Cash flow from money_movements
    mov_q = db.query(MoneyMovement).filter(
        MoneyMovement.date >= datetime.combine(date_from, datetime.min.time()),
        MoneyMovement.date <= datetime.combine(date_to, datetime.max.time()),
    )
    if payment_type:
        mov_q = mov_q.filter(MoneyMovement.payment_type == payment_type)
    movements = mov_q.all()

    cash_income = sum(m.amount for m in movements if m.direction == "income" and m.payment_type == "cash")
    cash_outgoing = sum(m.amount for m in movements if m.direction == "outgoing" and m.payment_type == "cash")
    bank_income = sum(m.amount for m in movements if m.direction == "income" and m.payment_type == "bank_transfer")
    bank_outgoing = sum(m.amount for m in movements if m.direction == "outgoing" and m.payment_type == "bank_transfer")

    return {
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "sales": {
            "count": len(sales),
            "total_sale_amount": total_sale_amount,
            "total_cost": total_cost,
            "total_profit": total_profit,
        },
        "purchases": {
            "count": len(purchases),
            "total_amount": total_purchase_amount,
        },
        "expenses": {
            "count": len(expenses),
            "total_amount": total_expense_amount,
            "by_category": expense_by_category,
        },
        "cash_flow": {
            "cash_income": cash_income,
            "cash_outgoing": cash_outgoing,
            "cash_net": cash_income - cash_outgoing,
            "bank_income": bank_income,
            "bank_outgoing": bank_outgoing,
            "bank_net": bank_income - bank_outgoing,
        },
        "net_profit": total_profit - total_expense_amount,
    }


@router.get("/daily-transactions")
def get_daily_transactions(
    date_val: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Tanlangan kun uchun barcha tranzaksiyalar tarixi."""
    
    start_of_day = datetime.combine(date_val, datetime.min.time())
    end_of_day = datetime.combine(date_val, datetime.max.time())
    
    # Calculate opening balance: all movements before start_of_day
    past_movements = db.query(MoneyMovement).filter(MoneyMovement.date < start_of_day).all()
    opening_cash = sum(m.amount if m.direction == "income" else -m.amount for m in past_movements if m.payment_type == "cash")
    opening_bank = sum(m.amount if m.direction == "income" else -m.amount for m in past_movements if m.payment_type == "bank_transfer")
    
    transactions = []
    
    # 1. Add all money movements for the day
    day_movements = db.query(MoneyMovement).filter(
        MoneyMovement.date >= start_of_day,
        MoneyMovement.date <= end_of_day
    ).all()
    
    cash_in = 0
    cash_out = 0
    bank_in = 0
    bank_out = 0
    
    MOVEMENT_LABELS = {
        "initial_balance": "Boshlang'ich balans",
        "purchase_payment": "Xarid to'lovi",
        "sale_payment": "Sotuv to'lovi",
        "customer_debt_payment": "Mijoz qarz to'lovi",
        "supplier_debt_payment": "Yetkazuvchi qarz to'lovi",
        "expense": "Xarajat",
        "balance_adjustment": "Balans tuzatish",
        "cancellation": "Bekor qilish",
    }
    
    for m in day_movements:
        if m.direction == "income":
            if m.payment_type == "cash": cash_in += m.amount
            if m.payment_type == "bank_transfer": bank_in += m.amount
        else:
            if m.payment_type == "cash": cash_out += m.amount
            if m.payment_type == "bank_transfer": bank_out += m.amount
            
        partner_name = "—"
        product_name = "—"
        quantity = None
        
        # Try to resolve partner/product if tied to sale or purchase
        if m.movement_type in ("sale_payment", "customer_debt_payment") and m.related_table == "sales" and m.related_id:
            s = db.query(Sale).filter(Sale.id == m.related_id).first()
            if s:
                partner_name = s.customer.name if s.customer else "—"
                product_name = s.product.name if s.product else "—"
        elif m.movement_type in ("purchase_payment", "supplier_debt_payment") and m.related_table == "purchases" and m.related_id:
            p = db.query(Purchase).filter(Purchase.id == m.related_id).first()
            if p:
                partner_name = p.supplier.name if p.supplier else "—"
                product_name = p.product.name if p.product else "—"
        elif m.movement_type == "expense" and m.related_table == "expenses" and m.related_id:
            e = db.query(Expense).filter(Expense.id == m.related_id).first()
            if e and e.category:
                product_name = e.category.name

        transactions.append({
            "time": m.date.strftime("%H:%M:%S"),
            "type": m.movement_type,
            "title": MOVEMENT_LABELS.get(m.movement_type, m.movement_type),
            "partner_name": partner_name,
            "product_name": product_name,
            "quantity": quantity,
            "amount": m.amount,
            "payment_type": "Naqd" if m.payment_type == "cash" else "Perechisleniya",
            "direction": m.direction,
            "note": m.note or "",
            "sort_time": m.date
        })

    # 2. Add operational sales for the day (stock out)
    sales = db.query(Sale).filter(Sale.date == date_val, Sale.status == "active").all()
    for s in sales:
        transactions.append({
            "time": s.created_at.strftime("%H:%M:%S"),
            "type": "sale",
            "title": "Sotuv (tovar chiqimi)",
            "partner_name": s.customer.name if s.customer else "—",
            "product_name": s.product.name if s.product else "—",
            "quantity": s.quantity_liters,
            "amount": s.total_sale_amount,
            "payment_type": "—",
            "direction": "stock_only",
            "note": s.note or "",
            "sort_time": s.created_at
        })

    # 3. Add operational purchases for the day (stock in)
    purchases = db.query(Purchase).filter(Purchase.date == date_val, Purchase.status == "active").all()
    for p in purchases:
        partner_name = p.supplier.name if p.supplier else "—"
        is_initial_stock = (partner_name == "O'zimiz (Boshlang'ich qoldiq)")
        
        transactions.append({
            "time": p.created_at.strftime("%H:%M:%S"),
            "type": "initial_stock" if is_initial_stock else "purchase",
            "title": "Boshlang'ich qoldiq kiritish" if is_initial_stock else "Prixod (tovar kirimi)",
            "partner_name": partner_name,
            "product_name": p.product.name if p.product else "—",
            "quantity": p.quantity_liters,
            "amount": p.total_amount,
            "payment_type": "—",
            "direction": "stock_only",
            "note": p.note or "",
            "sort_time": p.created_at
        })
        
    # Sort all transactions by time
    transactions.sort(key=lambda x: x["sort_time"])
    
    # Remove sort_time before returning
    for t in transactions:
        del t["sort_time"]

    return {
        "date": str(date_val),
        "opening_balance": {
            "cash": opening_cash,
            "bank_transfer": opening_bank,
            "total": opening_cash + opening_bank
        },
        "transactions": transactions,
        "totals": {
            "cash_in": cash_in,
            "cash_out": cash_out,
            "bank_in": bank_in,
            "bank_out": bank_out,
            "total_income": cash_in + bank_in,
            "total_outgoing": cash_out + bank_out
        },
        "closing_balance": {
            "cash": opening_cash + cash_in - cash_out,
            "bank_transfer": opening_bank + bank_in - bank_out,
            "total": (opening_cash + cash_in - cash_out) + (opening_bank + bank_in - bank_out)
        }
    }