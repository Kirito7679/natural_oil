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

    # Today's sales
    today_sales = db.query(Sale).filter(
        Sale.date == today, Sale.status == "active"
    ).all()
    today_sale_amount = sum(s.total_sale_amount for s in today_sales)
    today_profit = sum(s.total_profit for s in today_sales)

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
            "sale_amount": today_sale_amount,
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