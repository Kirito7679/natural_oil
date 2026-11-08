"""Ҳисобот бўлими — таблар учун API.

Ҳар бир таб ўз endpoint'ига эга, ҳаммаси сана оралиғи (date_from, date_to) билан ишлайди:
  /api/reports/tabs/transactions  — пул ҳаракатлари (транзакциялар)
  /api/reports/tabs/cashflow      — кунлик кирим-чиқим ва қолдиқ
  /api/reports/tabs/profit        — фойда / зарар (маҳсулот ва кун бўйича)
  /api/reports/tabs/expenses      — харажатлар (категория бўйича)
  /api/reports/tabs/sales         — сотувлар (маҳсулот ва мижоз бўйича)
  /api/reports/tabs/purchases     — приходлар (маҳсулот ва етказиб берувчи бўйича)
  /api/reports/tabs/debts         — қарздорлик (ҳамкор бўйича)
  /api/reports/tabs/inventory     — омбор (қолдиқ, кирим/чиқим литрда)
"""
import io
from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.debt import CustomerDebt, SupplierDebt, DebtPayment
from app.models.expense import Expense
from app.models.inventory import InventoryBatch
from app.models.money_movement import MoneyMovement
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.user import User
from app.services.formatting_service import get_rich_description
from app.services.purchase_service import INITIAL_STOCK_SUPPLIER_NAMES
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/reports/tabs", tags=["Report tabs"])

MOVEMENT_LABELS = {
    "initial_balance": "Бошланғич баланс",
    "purchase_payment": "Приход тўлови",
    "sale_payment": "Сотув тўлови",
    "customer_debt_payment": "Мижоз қарз тўлови",
    "supplier_debt_payment": "Етказиб берувчига қарз тўлови",
    "expense": "Харажат",
    "balance_adjustment": "Баланс тузатиш",
    "cancellation": "Бекор қилиш",
}
PAY_LABEL = {"cash": "Нақд", "bank_transfer": "Перечисления"}


def _range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    today = date.today()
    return (date_from or today.replace(day=1), date_to or today)


# Pul harakatlari UTC'da saqlanadi; hisobotda kompyuterning mahalliy vaqti (Toshkent) ko'rsatiladi
LOCAL_OFFSET = datetime.now().astimezone().utcoffset() or timedelta(0)


def _local(dt: datetime) -> datetime:
    return dt + LOCAL_OFFSET


def _dt_bounds(d1: date, d2: date) -> tuple[datetime, datetime]:
    """Mahalliy kun chegaralarini UTC'ga o'tkazadi."""
    return (datetime.combine(d1, datetime.min.time()) - LOCAL_OFFSET,
            datetime.combine(d2, datetime.max.time()) - LOCAL_OFFSET)


def _r(x: float) -> float:
    return round(x or 0.0, 2)


def _signed(m: MoneyMovement) -> float:
    return m.amount if m.direction == "income" else -m.amount


def _is_initial(purchase: Purchase) -> bool:
    return bool(purchase.supplier and purchase.supplier.name in INITIAL_STOCK_SUPPLIER_NAMES)


def _movement_context(db: Session, m: MoneyMovement) -> tuple[str, str]:
    """Пул ҳаракатига тегишли ҳамкор ва маҳсулот/категория номи."""
    partner, item = "—", "—"
    if m.related_table == "sales" and m.related_id:
        s = db.get(Sale, m.related_id)
        if s:
            partner = s.customer.name if s.customer else "—"
            item = s.product.name if s.product else "—"
    elif m.related_table == "purchases" and m.related_id:
        p = db.get(Purchase, m.related_id)
        if p:
            partner = p.supplier.name if p.supplier else "—"
            item = p.product.name if p.product else "—"
    elif m.related_table == "debt_payments" and m.related_id:
        dp = db.get(DebtPayment, m.related_id)
        if dp:
            if dp.debt_type == "customer_debt":
                debt = db.get(CustomerDebt, dp.debt_id)
                partner = debt.customer.name if debt and debt.customer else "—"
            else:
                debt = db.get(SupplierDebt, dp.debt_id)
                partner = debt.supplier.name if debt and debt.supplier else "—"
    elif m.related_table == "expenses" and m.related_id:
        e = db.get(Expense, m.related_id)
        if e and e.category:
            item = e.category.name
    return partner, item


# ── 1. Транзакциялар ─────────────────────────────────────────────────────────
@router.get("/transactions")
def tab_transactions(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    payment_type: str | None = Query(None),
    direction: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    start, end = _dt_bounds(d1, d2)
    q = db.query(MoneyMovement).filter(MoneyMovement.date >= start, MoneyMovement.date <= end)
    if payment_type:
        q = q.filter(MoneyMovement.payment_type == payment_type)
    if direction:
        q = q.filter(MoneyMovement.direction == direction)
    rows, income, outgoing = [], 0.0, 0.0
    for m in q.order_by(MoneyMovement.date.desc(), MoneyMovement.id.desc()).all():
        partner, item = _movement_context(db, m)
        if m.direction == "income":
            income += m.amount
        else:
            outgoing += m.amount
        rows.append({
            "id": m.id,
            "datetime": _local(m.date).strftime("%d.%m.%Y %H:%M"),
            "type": m.movement_type,
            "type_label": MOVEMENT_LABELS.get(m.movement_type, m.movement_type),
            "description": get_rich_description(db, m),
            "partner": partner,
            "item": item,
            "payment_type": m.payment_type,
            "payment_label": PAY_LABEL.get(m.payment_type, m.payment_type),
            "direction": m.direction,
            "amount": _r(m.amount),
        })
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {"count": len(rows), "income": _r(income), "outgoing": _r(outgoing), "net": _r(income - outgoing)},
        "rows": rows,
    }


# ── 2. Кирим-чиқим (кунлик) ─────────────────────────────────────────────────
@router.get("/cashflow")
def tab_cashflow(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    start, end = _dt_bounds(d1, d2)
    before = db.query(MoneyMovement).filter(MoneyMovement.date < start).all()
    open_cash = sum(_signed(m) for m in before if m.payment_type == "cash")
    open_bank = sum(_signed(m) for m in before if m.payment_type == "bank_transfer")

    days = defaultdict(lambda: {"cash_in": 0.0, "cash_out": 0.0, "bank_in": 0.0, "bank_out": 0.0})
    by_type = defaultdict(lambda: {"income": 0.0, "outgoing": 0.0})
    for m in db.query(MoneyMovement).filter(MoneyMovement.date >= start, MoneyMovement.date <= end).all():
        key = _local(m.date).date()
        acc = "cash" if m.payment_type == "cash" else "bank"
        days[key][f"{acc}_{'in' if m.direction == 'income' else 'out'}"] += m.amount
        by_type[m.movement_type]["income" if m.direction == "income" else "outgoing"] += m.amount

    rows, cash, bank = [], open_cash, open_bank
    d = d1
    while d <= d2:
        v = days.get(d)
        if v:
            cash += v["cash_in"] - v["cash_out"]
            bank += v["bank_in"] - v["bank_out"]
            rows.append({
                "date": d.strftime("%d.%m.%Y"),
                **{k: _r(x) for k, x in v.items()},
                "income": _r(v["cash_in"] + v["bank_in"]),
                "outgoing": _r(v["cash_out"] + v["bank_out"]),
                "net": _r(v["cash_in"] + v["bank_in"] - v["cash_out"] - v["bank_out"]),
                "closing_cash": _r(cash),
                "closing_bank": _r(bank),
                "closing_total": _r(cash + bank),
            })
        d += timedelta(days=1)

    tot = {k: _r(sum(r[k] for r in rows)) for k in ("cash_in", "cash_out", "bank_in", "bank_out", "income", "outgoing", "net")}
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "opening": {"cash": _r(open_cash), "bank_transfer": _r(open_bank), "total": _r(open_cash + open_bank)},
        "closing": {"cash": _r(cash), "bank_transfer": _r(bank), "total": _r(cash + bank)},
        "totals": tot,
        "by_type": [
            {"type": t, "label": MOVEMENT_LABELS.get(t, t), "income": _r(v["income"]), "outgoing": _r(v["outgoing"])}
            for t, v in sorted(by_type.items(), key=lambda kv: -(kv[1]["income"] + kv[1]["outgoing"]))
        ],
        "rows": rows,
    }


def _active_sales(db: Session, d1: date, d2: date) -> list[Sale]:
    return db.query(Sale).filter(Sale.date >= d1, Sale.date <= d2, Sale.status == "active").order_by(Sale.date.desc(), Sale.id.desc()).all()


def _active_expenses(db: Session, d1: date, d2: date) -> list[Expense]:
    return db.query(Expense).filter(Expense.date >= d1, Expense.date <= d2, Expense.status == "active").order_by(Expense.date.desc(), Expense.id.desc()).all()


# ── 3. Фойда / зарар ─────────────────────────────────────────────────────────
@router.get("/profit")
def tab_profit(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    sales = _active_sales(db, d1, d2)
    expenses = _active_expenses(db, d1, d2)

    by_product = defaultdict(lambda: {"liters": 0.0, "revenue": 0.0, "cost": 0.0, "profit": 0.0, "count": 0})
    by_day = defaultdict(lambda: {"revenue": 0.0, "cost": 0.0, "gross": 0.0, "expenses": 0.0})
    loss_sales = []
    for s in sales:
        name = s.product.name if s.product else "—"
        p = by_product[name]
        p["liters"] += s.quantity_liters
        p["revenue"] += s.total_sale_amount
        p["cost"] += s.total_cost
        p["profit"] += s.total_profit
        p["count"] += 1
        dd = by_day[s.date]
        dd["revenue"] += s.total_sale_amount
        dd["cost"] += s.total_cost
        dd["gross"] += s.total_profit
        if s.total_profit < 0:
            loss_sales.append({
                "id": s.id, "date": s.date.strftime("%d.%m.%Y"),
                "customer": s.customer.name if s.customer else "—", "product": name,
                "liters": _r(s.quantity_liters), "cost_price": _r(s.purchase_price_per_liter),
                "sale_price": _r(s.sale_price_per_liter), "profit": _r(s.total_profit),
            })
    for e in expenses:
        by_day[e.date]["expenses"] += e.amount

    revenue = sum(s.total_sale_amount for s in sales)
    cost = sum(s.total_cost for s in sales)
    gross = sum(s.total_profit for s in sales)
    exp_total = sum(e.amount for e in expenses)
    net = gross - exp_total
    liters = sum(s.quantity_liters for s in sales)

    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {
            "revenue": _r(revenue), "cost": _r(cost), "gross_profit": _r(gross),
            "expenses": _r(exp_total), "net_profit": _r(net),
            "gross_margin": _r(gross / revenue * 100) if revenue else 0,
            "net_margin": _r(net / revenue * 100) if revenue else 0,
            "liters": _r(liters), "profit_per_liter": _r(gross / liters) if liters else 0,
            "sale_count": len(sales),
        },
        "by_product": sorted([
            {
                "product": k, "liters": _r(v["liters"]), "revenue": _r(v["revenue"]), "cost": _r(v["cost"]),
                "profit": _r(v["profit"]), "count": v["count"],
                "avg_sale_price": _r(v["revenue"] / v["liters"]) if v["liters"] else 0,
                "avg_cost_price": _r(v["cost"] / v["liters"]) if v["liters"] else 0,
                "margin": _r(v["profit"] / v["revenue"] * 100) if v["revenue"] else 0,
            } for k, v in by_product.items()
        ], key=lambda r: -r["profit"]),
        "by_day": [
            {"date": k.strftime("%d.%m.%Y"), **{x: _r(y) for x, y in v.items()}, "net": _r(v["gross"] - v["expenses"])}
            for k, v in sorted(by_day.items(), reverse=True)
        ],
        "loss_sales": loss_sales,
    }


# ── 4. Харажатлар ────────────────────────────────────────────────────────────
@router.get("/expenses")
def tab_expenses(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    expenses = _active_expenses(db, d1, d2)
    total = sum(e.amount for e in expenses)
    by_cat = defaultdict(lambda: {"amount": 0.0, "count": 0})
    by_pay = defaultdict(float)
    for e in expenses:
        c = by_cat[e.category.name if e.category else "—"]
        c["amount"] += e.amount
        c["count"] += 1
        by_pay[e.payment_type] += e.amount
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {
            "amount": _r(total), "count": len(expenses),
            "cash": _r(by_pay.get("cash", 0)), "bank_transfer": _r(by_pay.get("bank_transfer", 0)),
            "daily_avg": _r(total / ((d2 - d1).days + 1)),
        },
        "by_category": sorted([
            {"category": k, "amount": _r(v["amount"]), "count": v["count"], "share": _r(v["amount"] / total * 100) if total else 0}
            for k, v in by_cat.items()
        ], key=lambda r: -r["amount"]),
        "rows": [
            {"id": e.id, "date": e.date.strftime("%d.%m.%Y"), "category": e.category.name if e.category else "—",
             "amount": _r(e.amount), "payment_label": PAY_LABEL.get(e.payment_type, e.payment_type), "note": e.note or ""}
            for e in expenses
        ],
    }


# ── 5. Сотувлар ──────────────────────────────────────────────────────────────
@router.get("/sales")
def tab_sales(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    sales = _active_sales(db, d1, d2)

    def group(key):
        g = defaultdict(lambda: {"liters": 0.0, "amount": 0.0, "paid": 0.0, "debt": 0.0, "profit": 0.0, "count": 0})
        for s in sales:
            v = g[key(s)]
            v["liters"] += s.quantity_liters
            v["amount"] += s.total_sale_amount
            v["paid"] += s.paid_amount
            v["debt"] += s.debt_amount
            v["profit"] += s.total_profit
            v["count"] += 1
        return sorted([{"name": k, **{x: _r(y) if x != "count" else y for x, y in v.items()}} for k, v in g.items()],
                      key=lambda r: -r["amount"])

    amount = sum(s.total_sale_amount for s in sales)
    liters = sum(s.quantity_liters for s in sales)
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {
            "count": len(sales), "liters": _r(liters), "amount": _r(amount),
            "paid": _r(sum(s.paid_amount for s in sales)), "debt": _r(sum(s.debt_amount for s in sales)),
            "profit": _r(sum(s.total_profit for s in sales)),
            "avg_price": _r(amount / liters) if liters else 0,
        },
        "by_product": group(lambda s: s.product.name if s.product else "—"),
        "by_customer": group(lambda s: s.customer.name if s.customer else "—"),
        "rows": [
            {"id": s.id, "date": s.date.strftime("%d.%m.%Y"), "customer": s.customer.name if s.customer else "—",
             "product": s.product.name if s.product else "—", "liters": _r(s.quantity_liters),
             "price": _r(s.sale_price_per_liter), "amount": _r(s.total_sale_amount), "paid": _r(s.paid_amount),
             "debt": _r(s.debt_amount), "profit": _r(s.total_profit)}
            for s in sales
        ],
    }


# ── 6. Приходлар ─────────────────────────────────────────────────────────────
@router.get("/purchases")
def tab_purchases(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    purchases = [
        p for p in db.query(Purchase).filter(Purchase.date >= d1, Purchase.date <= d2, Purchase.status == "active")
        .order_by(Purchase.date.desc(), Purchase.id.desc()).all()
        if not _is_initial(p)
    ]

    def group(key):
        g = defaultdict(lambda: {"liters": 0.0, "amount": 0.0, "paid": 0.0, "debt": 0.0, "count": 0})
        for p in purchases:
            v = g[key(p)]
            v["liters"] += p.quantity_liters
            v["amount"] += p.total_amount
            v["paid"] += p.paid_amount
            v["debt"] += p.debt_amount
            v["count"] += 1
        out = []
        for k, v in g.items():
            row = {"name": k, **{x: _r(y) if x != "count" else y for x, y in v.items()}}
            row["avg_price"] = _r(v["amount"] / v["liters"]) if v["liters"] else 0
            out.append(row)
        return sorted(out, key=lambda r: -r["amount"])

    amount = sum(p.total_amount for p in purchases)
    liters = sum(p.quantity_liters for p in purchases)
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {
            "count": len(purchases), "liters": _r(liters), "amount": _r(amount),
            "paid": _r(sum(p.paid_amount for p in purchases)), "debt": _r(sum(p.debt_amount for p in purchases)),
            "avg_price": _r(amount / liters) if liters else 0,
        },
        "by_product": group(lambda p: p.product.name if p.product else "—"),
        "by_supplier": group(lambda p: p.supplier.name if p.supplier else "—"),
        "rows": [
            {"id": p.id, "date": p.date.strftime("%d.%m.%Y"), "supplier": p.supplier.name if p.supplier else "—",
             "product": p.product.name if p.product else "—", "liters": _r(p.quantity_liters),
             "price": _r(p.purchase_price_per_liter), "amount": _r(p.total_amount),
             "paid": _r(p.paid_amount), "debt": _r(p.debt_amount)}
            for p in purchases
        ],
    }


# ── 7. Қарздорлик ────────────────────────────────────────────────────────────
@router.get("/debts")
def tab_debts(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    today = date.today()

    def debt_date(d) -> date:
        if getattr(d, "manual_date", None):
            return d.manual_date
        return d.created_at.date() if d.created_at else today

    def group(debts, partner_attr):
        g = {}
        for d in debts:
            partner = getattr(d, partner_attr)
            name = partner.name if partner else "—"
            v = g.setdefault(name, {"name": name, "phone": partner.phone if partner else "",
                                    "count": 0, "original": 0.0, "paid": 0.0, "remaining": 0.0, "oldest": None})
            v["count"] += 1
            v["original"] += d.original_amount
            v["paid"] += d.paid_amount
            v["remaining"] += d.remaining_amount
            dd = debt_date(d)
            if v["oldest"] is None or dd < v["oldest"]:
                v["oldest"] = dd
        out = []
        for v in g.values():
            oldest = v.pop("oldest")
            out.append({**{k: _r(x) if isinstance(x, float) else x for k, x in v.items()},
                        "oldest_date": oldest.strftime("%d.%m.%Y") if oldest else "—",
                        "days": (today - oldest).days if oldest else 0})
        return sorted(out, key=lambda r: -r["remaining"])

    cust = db.query(CustomerDebt).filter(CustomerDebt.status == "active", CustomerDebt.remaining_amount > 0.01).all()
    supp = db.query(SupplierDebt).filter(SupplierDebt.status == "active", SupplierDebt.remaining_amount > 0.01).all()

    pays = db.query(DebtPayment).filter(DebtPayment.date >= d1, DebtPayment.date <= d2, DebtPayment.status == "active").all()
    received = sum(p.amount for p in pays if p.debt_type == "customer_debt")
    paid_out = sum(p.amount for p in pays if p.debt_type == "supplier_debt")

    new_cust = sum(d.original_amount for d in db.query(CustomerDebt).filter(CustomerDebt.status != "cancelled").all() if d1 <= debt_date(d) <= d2)
    new_supp = sum(d.original_amount for d in db.query(SupplierDebt).filter(SupplierDebt.status != "cancelled").all() if d1 <= debt_date(d) <= d2)

    customer_total = sum(d.remaining_amount for d in cust)
    supplier_total = sum(d.remaining_amount for d in supp)
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {
            "customer_total": _r(customer_total), "supplier_total": _r(supplier_total),
            "net": _r(customer_total - supplier_total),
            "period_new_customer": _r(new_cust), "period_received": _r(received),
            "period_new_supplier": _r(new_supp), "period_paid_out": _r(paid_out),
        },
        "customers": group(cust, "customer"),
        "suppliers": group(supp, "supplier"),
    }


# ── 8. Омбор ─────────────────────────────────────────────────────────────────
@router.get("/inventory")
def tab_inventory(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    d1, d2 = _range(date_from, date_to)
    products = {p.id: p.name for p in db.query(Product).all()}
    stock = defaultdict(lambda: {"liters": 0.0, "value": 0.0, "batches": 0})
    batches = db.query(InventoryBatch).filter(InventoryBatch.status == "active", InventoryBatch.remaining_quantity_liters > 0).all()
    for b in batches:
        v = stock[b.product_id]
        v["liters"] += b.remaining_quantity_liters
        v["value"] += b.remaining_quantity_liters * b.purchase_price_per_liter
        v["batches"] += 1

    moved_in = defaultdict(float)
    for p in db.query(Purchase).filter(Purchase.date >= d1, Purchase.date <= d2, Purchase.status == "active").all():
        moved_in[p.product_id] += p.quantity_liters
    moved_out = defaultdict(float)
    for s in _active_sales(db, d1, d2):
        moved_out[s.product_id] += s.quantity_liters

    rows = []
    for pid in sorted(set(stock) | set(moved_in) | set(moved_out), key=lambda i: products.get(i, "")):
        v = stock.get(pid, {"liters": 0.0, "value": 0.0, "batches": 0})
        rows.append({
            "product": products.get(pid, "—"), "liters": _r(v["liters"]), "value": _r(v["value"]),
            "avg_cost": _r(v["value"] / v["liters"]) if v["liters"] else 0, "batches": v["batches"],
            "period_in": _r(moved_in.get(pid, 0)), "period_out": _r(moved_out.get(pid, 0)),
        })
    return {
        "period": {"from": str(d1), "to": str(d2)},
        "totals": {
            "liters": _r(sum(r["liters"] for r in rows)), "value": _r(sum(r["value"] for r in rows)),
            "period_in": _r(sum(r["period_in"] for r in rows)), "period_out": _r(sum(r["period_out"] for r in rows)),
            "batches": len(batches),
        },
        "by_product": rows,
        "batches": [
            {"id": b.id, "product": products.get(b.product_id, "—"), "supplier": b.supplier.name if b.supplier else "—",
             "price": _r(b.purchase_price_per_liter), "initial": _r(b.initial_quantity_liters),
             "remaining": _r(b.remaining_quantity_liters),
             "used_pct": _r((1 - b.remaining_quantity_liters / b.initial_quantity_liters) * 100) if b.initial_quantity_liters else 0,
             "value": _r(b.remaining_quantity_liters * b.purchase_price_per_liter),
             "created": b.created_at.strftime("%d.%m.%Y") if b.created_at else "—"}
            for b in sorted(batches, key=lambda b: b.created_at or datetime.min)
        ],
    }


# ── 9. Маҳсулот статистикаси ─────────────────────────────────────────────────
def _bucket(d: date, grain: str) -> tuple[date, str]:
    if grain == "month":
        start = d.replace(day=1)
        return start, start.strftime("%m.%Y")
    if grain == "week":
        start = d - timedelta(days=d.weekday())
        return start, start.strftime("%d.%m")
    return d, d.strftime("%d.%m")


@router.get("/products")
def tab_products(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Qaysi mahsulot ko'proq/kamroq sotilgan va foyda keltirgan, vaqt bo'yicha dinamika."""
    d1, d2 = _range(date_from, date_to)
    days = (d2 - d1).days + 1
    grain = "day" if days <= 31 else "week" if days <= 120 else "month"

    # Oldingi teng davr (o'sish foizi uchun)
    p2 = d1 - timedelta(days=1)
    p1 = p2 - timedelta(days=days - 1)

    sales = _active_sales(db, d1, d2)
    prev = _active_sales(db, p1, p2)
    products = db.query(Product).order_by(Product.name).all()

    def agg(rows):
        g = defaultdict(lambda: {"liters": 0.0, "revenue": 0.0, "profit": 0.0, "count": 0, "last": None})
        for s in rows:
            v = g[s.product_id]
            v["liters"] += s.quantity_liters
            v["revenue"] += s.total_sale_amount
            v["profit"] += s.total_profit
            v["count"] += 1
            if v["last"] is None or s.date > v["last"]:
                v["last"] = s.date
        return g

    cur, old = agg(sales), agg(prev)
    tot_l = sum(v["liters"] for v in cur.values())
    tot_p = sum(v["profit"] for v in cur.values())

    # Vaqt bo'yicha: barcha bucket'lar (bo'shlari ham), mahsulot kesimida
    buckets: dict[date, str] = {}
    d = d1
    while d <= d2:
        k, label = _bucket(d, grain)
        buckets.setdefault(k, label)
        d += timedelta(days=1)
    series = defaultdict(lambda: defaultdict(lambda: {"liters": 0.0, "profit": 0.0, "revenue": 0.0}))
    for s in sales:
        k, _l = _bucket(s.date, grain)
        for key in (s.product_id, "all"):
            b = series[key][k]
            b["liters"] += s.quantity_liters
            b["profit"] += s.total_profit
            b["revenue"] += s.total_sale_amount

    def growth(now, before):
        if before == 0:
            return None
        return _r((now - before) / abs(before) * 100)

    rows = []
    for p in products:
        v = cur.get(p.id)
        o = old.get(p.id, {"liters": 0.0, "profit": 0.0})
        if v is None and not p.is_active:
            continue
        v = v or {"liters": 0.0, "revenue": 0.0, "profit": 0.0, "count": 0, "last": None}
        best_k = max(series[p.id], key=lambda k: series[p.id][k]["liters"], default=None) if p.id in series else None
        rows.append({
            "product_id": p.id, "product": p.name,
            "liters": _r(v["liters"]), "revenue": _r(v["revenue"]), "profit": _r(v["profit"]), "count": v["count"],
            "margin": _r(v["profit"] / v["revenue"] * 100) if v["revenue"] else 0,
            "profit_per_liter": _r(v["profit"] / v["liters"]) if v["liters"] else 0,
            "liters_share": _r(v["liters"] / tot_l * 100) if tot_l else 0,
            "profit_share": _r(v["profit"] / tot_p * 100) if tot_p else 0,
            "avg_daily_liters": _r(v["liters"] / days),
            "liters_growth": growth(v["liters"], o["liters"]),
            "profit_growth": growth(v["profit"], o["profit"]),
            "last_sale": v["last"].strftime("%d.%m.%Y") if v["last"] else None,
            "best_period": buckets.get(best_k) if best_k else None,
        })

    sold = [r for r in rows if r["count"] > 0]

    def pick(key, reverse):
        if not sold:
            return None
        r = sorted(sold, key=lambda x: x[key], reverse=reverse)[0]
        return {"product": r["product"], "liters": r["liters"], "profit": r["profit"], "revenue": r["revenue"], "margin": r["margin"]}

    return {
        "period": {"from": str(d1), "to": str(d2), "prev_from": str(p1), "prev_to": str(p2), "grain": grain},
        "highlights": {
            "most_sold": pick("liters", True),
            "least_sold": pick("liters", False) if len(sold) > 1 else None,
            "most_profit": pick("profit", True),
            "least_profit": pick("profit", False) if len(sold) > 1 else None,
            "best_margin": pick("margin", True),
        },
        "unsold": [r["product"] for r in rows if r["count"] == 0],
        "ranking": sorted(rows, key=lambda r: (-r["liters"], r["product"])),
        "timeline": {
            "labels": [buckets[k] for k in sorted(buckets)],
            "series": {
                str(pid): [{"liters": _r(series[pid][k]["liters"]), "profit": _r(series[pid][k]["profit"]),
                            "revenue": _r(series[pid][k]["revenue"])} for k in sorted(buckets)]
                for pid in list(series.keys())
            },
        },
    }


# ── Excel: joriy tab, tanlangan sana va filtrlar bo'yicha ────────────────────

M, L, P, T, N = "money", "liters", "pct", "text", "int"

TAB_TITLES = {
    "transactions": "Транзакциялар", "cashflow": "Кирим-чиқим", "profit": "Фойда ва зарар",
    "products": "Маҳсулот статистикаси", "expenses": "Харажатлар", "sales": "Сотувлар",
    "purchases": "Приходлар", "debts": "Қарздорлик", "inventory": "Омбор",
}
DIR_LABEL = {"income": "Фақат кирим", "outgoing": "Фақат чиқим"}

# Har bir tab: (KPI ro'yxati, jadvallar ro'yxati)
EXCEL_SPECS = {
    "transactions": (
        [("totals.income", "Жами кирим", M), ("totals.outgoing", "Жами чиқим", M), ("totals.net", "Соф пул оқими", M), ("totals.count", "Операциялар сони", N)],
        [("Транзакциялар", "rows", [("datetime", "Сана / вақт", T), ("type_label", "Тур", T), ("partner", "Ҳамкор", T),
                                    ("item", "Маҳсулот / категория", T), ("payment_label", "Ҳисоб", T),
                                    ("direction_label", "Йўналиш", T), ("signed_amount", "Сумма", M), ("description", "Изоҳ", T)])],
    ),
    "cashflow": (
        [("opening.total", "Давр боши қолдиғи", M), ("totals.income", "Кирим", M), ("totals.outgoing", "Чиқим", M), ("closing.total", "Давр охири қолдиғи", M)],
        [("Кунлар бўйича", "rows", [("date", "Сана", T), ("cash_in", "Нақд кирим", M), ("cash_out", "Нақд чиқим", M), ("bank_in", "Банк кирим", M),
                                    ("bank_out", "Банк чиқим", M), ("net", "Кунлик натижа", M), ("closing_total", "Кун охири қолдиқ", M)]),
         ("Операция турлари бўйича", "by_type", [("label", "Тур", T), ("income", "Кирим", M), ("outgoing", "Чиқим", M)])],
    ),
    "profit": (
        [("totals.revenue", "Жами савдо", M), ("totals.cost", "Таннарх", M), ("totals.gross_profit", "Ялпи фойда", M),
         ("totals.expenses", "Харажатлар", M), ("totals.net_profit", "Соф натижа", M), ("totals.net_margin", "Соф маржа, %", P)],
        [("Маҳсулотлар бўйича", "by_product", [("product", "Маҳсулот", T), ("liters", "Сотилди, л", L), ("avg_cost_price", "Ўрт. кирим нархи", M),
                                               ("avg_sale_price", "Ўрт. сотиш нархи", M), ("revenue", "Савдо", M), ("profit", "Фойда", M), ("margin", "Маржа, %", P)]),
         ("Кунлар бўйича", "by_day", [("date", "Сана", T), ("revenue", "Савдо", M), ("gross", "Ялпи фойда", M), ("expenses", "Харажат", M), ("net", "Соф натижа", M)]),
         ("Зарар билан сотилганлар", "loss_sales", [("date", "Сана", T), ("customer", "Мижоз", T), ("product", "Маҳсулот", T), ("liters", "Миқдор, л", L),
                                                    ("cost_price", "Кирим нархи", M), ("sale_price", "Сотиш нархи", M), ("profit", "Зарар", M)])],
    ),
    "products": (
        [],
        [("Маҳсулотлар рейтинги", "ranking", [("product", "Маҳсулот", T), ("liters", "Сотилди, л", L), ("liters_share", "Ҳажм улуши, %", P),
                                               ("liters_growth", "Ўсиш (л), %", P), ("revenue", "Савдо", M), ("profit", "Фойда", M),
                                               ("profit_share", "Фойда улуши, %", P), ("profit_growth", "Ўсиш (фойда), %", P),
                                               ("profit_per_liter", "1 л фойда", M), ("avg_daily_liters", "Кунига, л", L),
                                               ("best_period", "Энг яхши давр", T), ("last_sale", "Охирги сотув", T)])],
    ),
    "expenses": (
        [("totals.amount", "Жами харажат", M), ("totals.cash", "Нақддан", M), ("totals.bank_transfer", "Перечислениядан", M), ("totals.daily_avg", "Кунига ўртача", M)],
        [("Категориялар бўйича", "by_category", [("category", "Категория", T), ("count", "Сони", N), ("amount", "Сумма", M), ("share", "Улуши, %", P)]),
         ("Барча харажатлар", "rows", [("date", "Сана", T), ("category", "Категория", T), ("payment_label", "Ҳисоб", T), ("amount", "Сумма", M), ("note", "Изоҳ", T)])],
    ),
    "sales": (
        [("totals.amount", "Сотув суммаси", M), ("totals.liters", "Сотилган, л", L), ("totals.paid", "Тўланган", M), ("totals.debt", "Қарзга", M), ("totals.profit", "Фойда", M)],
        [("Маҳсулотлар бўйича", "by_product", [("name", "Маҳсулот", T), ("count", "Сони", N), ("liters", "Миқдор, л", L), ("amount", "Сумма", M),
                                               ("paid", "Тўланган", M), ("debt", "Қарз", M), ("profit", "Фойда", M)]),
         ("Мижозлар бўйича", "by_customer", [("name", "Мижоз", T), ("count", "Сони", N), ("liters", "Миқдор, л", L), ("amount", "Сумма", M),
                                             ("paid", "Тўланган", M), ("debt", "Қарз", M), ("profit", "Фойда", M)]),
         ("Барча сотувлар", "rows", [("date", "Сана", T), ("customer", "Мижоз", T), ("product", "Маҳсулот", T), ("liters", "Миқдор, л", L),
                                     ("price", "Нарх", M), ("amount", "Сумма", M), ("paid", "Тўланган", M), ("debt", "Қарз", M), ("profit", "Фойда", M)])],
    ),
    "purchases": (
        [("totals.amount", "Приход суммаси", M), ("totals.liters", "Келган, л", L), ("totals.paid", "Тўланган", M), ("totals.debt", "Қарзга", M)],
        [("Маҳсулотлар бўйича", "by_product", [("name", "Маҳсулот", T), ("count", "Сони", N), ("liters", "Миқдор, л", L), ("amount", "Сумма", M),
                                               ("paid", "Тўланган", M), ("debt", "Қарз", M), ("avg_price", "Ўрт. нарх", M)]),
         ("Етказиб берувчилар бўйича", "by_supplier", [("name", "Етказиб берувчи", T), ("count", "Сони", N), ("liters", "Миқдор, л", L),
                                                       ("amount", "Сумма", M), ("paid", "Тўланган", M), ("debt", "Қарз", M), ("avg_price", "Ўрт. нарх", M)]),
         ("Барча приходлар", "rows", [("date", "Сана", T), ("supplier", "Етказиб берувчи", T), ("product", "Маҳсулот", T), ("liters", "Миқдор, л", L),
                                      ("price", "1 л нархи", M), ("amount", "Сумма", M), ("paid", "Тўланган", M), ("debt", "Қарз", M)])],
    ),
    "debts": (
        [("totals.customer_total", "Мижозлар бизга қарз", M), ("totals.supplier_total", "Бизнинг қарзимиз", M), ("totals.net", "Соф ҳолат", M)],
        [("Мижозлар қарзи", "customers", [("name", "Мижоз", T), ("phone", "Телефон", T), ("count", "Қарзлар", N), ("original", "Дастлабки", M),
                                          ("paid", "Тўланган", M), ("remaining", "Қолган", M), ("oldest_date", "Энг эски", T), ("days", "Кун", N)]),
         ("Етказиб берувчиларга қарзимиз", "suppliers", [("name", "Етказиб берувчи", T), ("phone", "Телефон", T), ("count", "Қарзлар", N),
                                                         ("original", "Дастлабки", M), ("paid", "Тўланган", M), ("remaining", "Қолган", M),
                                                         ("oldest_date", "Энг эски", T), ("days", "Кун", N)])],
    ),
    "inventory": (
        [("totals.liters", "Омбордаги ёқилғи, л", L), ("totals.value", "Омбор қиймати", M), ("totals.period_in", "Даврда кирди, л", L), ("totals.period_out", "Даврда чиқди, л", L)],
        [("Маҳсулотлар бўйича", "by_product", [("product", "Маҳсулот", T), ("liters", "Қолдиқ, л", L), ("avg_cost", "Ўрт. таннарх", M), ("value", "Қиймати", M),
                                               ("period_in", "Даврда кирди, л", L), ("period_out", "Даврда чиқди, л", L), ("batches", "Партиялар", N)]),
         ("Фаол партиялар", "batches", [("id", "№", N), ("created", "Келган", T), ("product", "Маҳсулот", T), ("supplier", "Етказиб берувчи", T),
                                        ("price", "1 л нархи", M), ("initial", "Дастлабки, л", L), ("remaining", "Қолдиқ, л", L),
                                        ("used_pct", "Сотилди, %", P), ("value", "Қиймати", M)])],
    ),
}

FMT = {M: '#,##0" сўм";[Red]-#,##0" сўм"', L: '#,##0.0" л"', P: '0.0"%"', N: '0', T: '@'}
BLACK = PatternFill("solid", fgColor="0B0B0B")
YELLOW = PatternFill("solid", fgColor="FBB805")
SOFT = PatternFill("solid", fgColor="FFF4D1")
THIN = Side(style="thin", color="E7E4DC")


def _get(d: dict, path: str):
    for part in path.split("."):
        d = d.get(part) if isinstance(d, dict) else None
    return d


def _build_excel(tab: str, data: dict, filters_text: str) -> Workbook:
    kpis, tables = EXCEL_SPECS[tab]
    wb = Workbook()
    ws = wb.active
    ws.title = TAB_TITLES[tab][:31]
    width = max([len(cols) for _t, _k, cols in tables] + [2])

    ws.append([f"NATURAL OIL PRODUCTS — {TAB_TITLES[tab].upper()}"])
    ws.cell(1, 1).font = Font(bold=True, size=15, color="FBB805")
    for c in range(1, width + 1):
        ws.cell(1, c).fill = BLACK
    ws.append([f"Давр: {data['period']['from']} — {data['period']['to']}"])
    ws.append([filters_text] if filters_text else [])
    ws.append([f"Тайёрланди: {datetime.now().strftime('%d.%m.%Y %H:%M')}"])
    for r in (2, 3, 4):
        ws.cell(r, 1).font = Font(italic=True, color="55524B")
    ws.append([])

    if kpis:
        ws.append(["ЖАМИ КЎРСАТКИЧЛАР"])
        ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
        for key, label, kind in kpis:
            ws.append([label, _get(data, key) or 0])
            c = ws.cell(ws.max_row, 2)
            c.number_format = FMT[kind]
            c.font = Font(bold=True)
            ws.cell(ws.max_row, 1).fill = SOFT
            c.fill = SOFT
        ws.append([])

    for title, key, cols in tables:
        rows = data.get(key) or []
        ws.append([f"{title} ({len(rows)} та)"])
        ws.cell(ws.max_row, 1).font = Font(bold=True, size=12)
        ws.append([label for _k, label, _t in cols])
        hr = ws.max_row
        for i in range(1, len(cols) + 1):
            cell = ws.cell(hr, i)
            cell.font = Font(bold=True, color="0B0B0B")
            cell.fill = YELLOW
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if not rows:
            ws.append(["Маълумот йўқ"])
        first = ws.max_row + 1
        for r in rows:
            ws.append([r.get(k) if r.get(k) is not None else ("" if t == T else None) for k, _l, t in cols])
            for i, (_k, _l, t) in enumerate(cols, start=1):
                cell = ws.cell(ws.max_row, i)
                cell.number_format = FMT[t]
                cell.border = Border(bottom=THIN)
        # Jami qatori (pul va litr ustunlari uchun SUM formulasi)
        if rows and any(t in (M, L) for _k, _l, t in cols):
            last = ws.max_row
            total_row = ["ЖАМИ"] + [None] * (len(cols) - 1)
            ws.append(total_row)
            tr = ws.max_row
            for i, (_k, _l, t) in enumerate(cols, start=1):
                cell = ws.cell(tr, i)
                cell.font = Font(bold=True)
                cell.fill = SOFT
                if i > 1 and t in (M, L):
                    col = get_column_letter(i)
                    cell.value = f"=SUM({col}{first}:{col}{last})"
                    cell.number_format = FMT[t]
        ws.append([])

    for i in range(1, width + 1):
        letter = get_column_letter(i)
        longest = max((len(str(c.value)) for c in ws[letter][5:] if c.value is not None and not str(c.value).startswith("=")), default=10)
        ws.column_dimensions[letter].width = min(max(longest + 3, 13), 48)
    ws.column_dimensions["A"].width = max(ws.column_dimensions["A"].width, 24)
    ws.freeze_panes = "A6"
    return wb


TAB_FUNCS = {
    "transactions": tab_transactions, "cashflow": tab_cashflow, "profit": tab_profit, "products": tab_products,
    "expenses": tab_expenses, "sales": tab_sales, "purchases": tab_purchases, "debts": tab_debts, "inventory": tab_inventory,
}


@router.get("/{tab}/excel")
def tab_excel(
    tab: str,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    payment_type: str | None = Query(None),
    direction: str | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Joriy tabni tanlangan sana va filtrlar bilan Excel'ga chiqaradi."""
    if tab not in TAB_FUNCS:
        raise HTTPException(status_code=404, detail="Бундай ҳисобот йўқ")
    kwargs = {"date_from": date_from, "date_to": date_to, "db": db, "_": user}
    if tab == "transactions":
        kwargs.update(payment_type=payment_type, direction=direction)
    data = TAB_FUNCS[tab](**kwargs)
    if tab == "transactions":
        for r in data["rows"]:
            r["direction_label"] = "Кирим" if r["direction"] == "income" else "Чиқим"
            r["signed_amount"] = r["amount"] if r["direction"] == "income" else -r["amount"]

    parts = []
    if tab == "transactions" and direction in DIR_LABEL:
        parts.append(DIR_LABEL[direction])
    if tab == "transactions" and payment_type in PAY_LABEL:
        parts.append(f"Ҳисоб: {PAY_LABEL[payment_type]}")
    filters_text = ("Филтр: " + ", ".join(parts)) if parts else ""

    wb = _build_excel(tab, data, filters_text)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    d1, d2 = data["period"]["from"], data["period"]["to"]
    suffix = f"_{direction}" if tab == "transactions" and direction else ""
    filename = f"natural_oil_{tab}{suffix}_{d1}_{d2}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
