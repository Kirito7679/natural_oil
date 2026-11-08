"""Excel export router — all ERP data exports with full filter support."""
import io
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from app.database import get_db
from app.models.user import User
from app.models.sale import Sale, SalePayment
from app.models.purchase import Purchase, PurchasePayment
from app.models.inventory import InventoryBatch
from app.models.debt import CustomerDebt, SupplierDebt
from app.models.expense import Expense
from app.models.money_movement import MoneyMovement
from app.models.balance import BalanceAccount
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/export", tags=["Excel Export"])


# ── Style helpers ───────────────────────────────────────────────────────────

HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill("solid", fgColor="1F3A5F")
SUMMARY_FONT = Font(bold=True, size=11)
SECTION_FONT = Font(bold=True, size=13)

def format_money(value: float | int | None) -> str:
    if value is None:
        return "0 сўм"
    try:
        val = int(round(value))
        # This will format with spaces, e.g. "10 000 000 so'm"
        return f"{val:,}".replace(",", " ") + " сўм"
    except Exception:
        return "0 сўм"

PAYMENT_LABELS = {"cash": "Нақд", "bank_transfer": "Перечисления"}
DIRECTION_LABELS = {"income": "Кирим", "outgoing": "Чиқим"}
STATUS_LABELS = {
    "active": "Фаол",
    "cancelled": "Бекор қилинган",
    "closed": "Ёпилган",
    "finished": "Тугаган",
}
MOVEMENT_LABELS = {
    "initial_balance": "Бошланғич баланс",
    "purchase_payment": "Харид тўлови",
    "sale_payment": "Сотув тўлови",
    "customer_debt_payment": "Мижоз қарз тўлови",
    "supplier_debt_payment": "Етказувчи қарз тўлови",
    "expense": "Харажат",
    "balance_adjustment": "Баланс тузатиш",
    "cancellation": "Бекор қилиш",
}
TABLE_LABELS = {
    "purchases": "Приход",
    "sales": "Сотув",
    "expenses": "Харажат",
    "debt_payments": "Қарз тўлови",
    "balance_accounts": "Баланс",
}


def style_header_row(ws, row=1):
    for cell in ws[row]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")


def auto_width(ws):
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                v = str(cell.value) if cell.value is not None else ""
                if len(v) > max_len:
                    max_len = len(v)
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 45)


# Removed format_money_columns since we format as strings


def make_response(wb: Workbook, filename: str) -> StreamingResponse:
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def today_str():
    return date.today().isoformat()


def get_purchase_payment_types(p: Purchase) -> str:
    """Combine payment types of a purchase as readable string."""
    if not p.payments:
        return "—"
    types = list({pp.payment_type for pp in p.payments if pp.status == "active"})
    return ", ".join(PAYMENT_LABELS.get(t, t) for t in types)


def get_sale_payment_types(s: Sale) -> str:
    if not s.payments:
        return "—"
    types = list({sp.payment_type for sp in s.payments if sp.status == "active"})
    return ", ".join(PAYMENT_LABELS.get(t, t) for t in types)


# ──────────────────────────────────────────────────────────────────────────────
# 1. GENERAL REPORT
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/general-report")
def export_general_report(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    # Fetch data
    sales = db.query(Sale).filter(
        Sale.date >= date_from, Sale.date <= date_to, Sale.status == "active"
    ).all()
    purchases = db.query(Purchase).filter(
        Purchase.date >= date_from, Purchase.date <= date_to, Purchase.status == "active"
    ).all()
    expenses = db.query(Expense).filter(
        Expense.date >= date_from, Expense.date <= date_to, Expense.status == "active"
    ).all()
    movements = db.query(MoneyMovement).filter(
        MoneyMovement.date >= datetime.combine(date_from, datetime.min.time()),
        MoneyMovement.date <= datetime.combine(date_to, datetime.max.time()),
    ).all()
    accounts = db.query(BalanceAccount).all()
    cust_debt = db.query(func.sum(CustomerDebt.remaining_amount)).filter(
        CustomerDebt.status == "active"
    ).scalar() or 0
    supp_debt = db.query(func.sum(SupplierDebt.remaining_amount)).filter(
        SupplierDebt.status == "active"
    ).scalar() or 0

    total_sale = sum(s.total_sale_amount for s in sales)
    total_cost = sum(s.total_cost for s in sales)
    total_profit = sum(s.total_profit for s in sales)
    total_expense = sum(e.amount for e in expenses)
    total_purchase = sum(p.total_amount for p in purchases)
    cash_in = sum(m.amount for m in movements if m.direction == "income" and m.payment_type == "cash")
    cash_out = sum(m.amount for m in movements if m.direction == "outgoing" and m.payment_type == "cash")
    bank_in = sum(m.amount for m in movements if m.direction == "income" and m.payment_type == "bank_transfer")
    bank_out = sum(m.amount for m in movements if m.direction == "outgoing" and m.payment_type == "bank_transfer")
    cash_bal = next((a.current_balance for a in accounts if a.type == "cash"), 0)
    bank_bal = next((a.current_balance for a in accounts if a.type == "bank_transfer"), 0)

    # Build workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Умумий ҳисобот"

    ws.append(["NATURAL OIL ERP — УМУМИЙ ҲИСОБОТ"])
    ws[1][0].font = SECTION_FONT
    ws.append([f"Сана оралиғи: {date_from} — {date_to}"])
    ws.append([])

    # Summary table
    summary_rows = [
        ("Жами сотув", total_sale),
        ("Жами таннарх", total_cost),
        ("Ялпи фойда", total_profit),
        ("Жами харажат", total_expense),
        ("Соф фойда", total_profit - total_expense),
        ("Жами харид", total_purchase),
        ("Мижозлар қарзи", cust_debt),
        ("Бизнинг қарзлар", supp_debt),
        ("Нақд кирим", cash_in),
        ("Нақд чиқим", cash_out),
        ("Нақд баланс (Ҳисобланган)", cash_in - cash_out),
        ("Перечисления кирим", bank_in),
        ("Перечисления чиқим", bank_out),
        ("Перечисления баланс (Ҳисобланган)", bank_in - bank_out),
        ("Нақд баланс", cash_bal),
        ("Перечисления баланс", bank_bal),
        ("Умумий баланс", cash_bal + bank_bal),
    ]
    ws.append(["Кўрсаткич", "Қиймат"])
    style_header_row(ws, ws.max_row)
    summary_start = ws.max_row
    for label, value in summary_rows:
        ws.append([label, format_money(value)])
        ws[ws.max_row][0].font = SUMMARY_FONT

    ws.freeze_panes = f"A{summary_start + 1}"
    ws.append([])
    ws.append([])

    # Sales table
    ws.append(["СОТУВЛАР"])
    ws[ws.max_row][0].font = SECTION_FONT
    ws.append(["Сана", "Мижоз", "Маҳсулот", "Миқдор (л)",
               "Сотиш нархи", "Сотув суммаси", "Фойда"])
    style_header_row(ws, ws.max_row)
    for s in sales:
        ws.append([
            str(s.date),
            s.customer.name if s.customer else "",
            s.product.name if s.product else "",
            s.quantity_liters,
            format_money(s.sale_price_per_liter),
            format_money(s.total_sale_amount),
            format_money(s.total_profit),
        ])
    if sales:
        ws.append([
            "ЖАМИ", "", "",
            sum(s.quantity_liters for s in sales),
            "",
            format_money(total_sale),
            format_money(total_profit),
        ])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    ws.append([])
    ws.append([])

    # Expenses by category
    expense_by_cat = {}
    for e in expenses:
        cat = e.category.name if e.category else "Бошқа"
        expense_by_cat[cat] = expense_by_cat.get(cat, 0) + e.amount

    ws.append(["ХАРАЖАТЛАР (КАТЕГОРИЯ БЎЙИЧА)"])
    ws[ws.max_row][0].font = SECTION_FONT
    ws.append(["Категория", "Сумма"])
    style_header_row(ws, ws.max_row)
    for cat, amt in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
        ws.append([cat, format_money(amt)])
    if expense_by_cat:
        ws.append(["ЖАМИ", format_money(total_expense)])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    ws.append([])
    ws.append([])

    # Cash flow
    ws.append(["ПУЛ ОҚИМИ"])
    ws[ws.max_row][0].font = SECTION_FONT
    ws.append(["Кўрсаткич", "Нақд", "Перечисления"])
    style_header_row(ws, ws.max_row)
    flow_rows = [
        ("Кирим", cash_in, bank_in),
        ("Чиқим", cash_out, bank_out),
        ("Баланс", cash_in - cash_out, bank_in - bank_out),
    ]
    for label, c, b in flow_rows:
        ws.append([label, format_money(c), format_money(b)])
        ws[ws.max_row][0].font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_general_report_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 2. SALES
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/sales")
def export_sales(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    customer_id: int | None = Query(None),
    product_id: int | None = Query(None),
    payment_type: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Sale).order_by(Sale.date.desc(), Sale.id.desc())
    if date_from:
        q = q.filter(Sale.date >= date_from)
    if date_to:
        q = q.filter(Sale.date <= date_to)
    if customer_id:
        q = q.filter(Sale.customer_id == customer_id)
    if product_id:
        q = q.filter(Sale.product_id == product_id)
    if status:
        q = q.filter(Sale.status == status)
    sales = q.all()

    if payment_type:
        sales = [s for s in sales if any(
            p.payment_type == payment_type and p.status == "active" for p in s.payments
        )]

    wb = Workbook()
    ws = wb.active
    ws.title = "Сотувлар"

    headers = [
        "Сана", "Мижоз", "Маҳсулот", "Омбор партияси", "Миқдор (л)",
        "Кирим нархи", "Сотиш нархи", "1 л фойда",
        "Умумий сотув", "Умумий таннарх", "Умумий фойда",
        "Тўланган", "Қарз", "Тўлов тури", "Статус", "Изоҳ",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    ws.freeze_panes = "A2"

    for s in sales:
        ws.append([
            str(s.date),
            s.customer.name if s.customer else "",
            s.product.name if s.product else "",
            f"#{s.inventory_batch_id}",
            s.quantity_liters,
            format_money(s.purchase_price_per_liter),
            format_money(s.sale_price_per_liter),
            format_money(s.profit_per_liter),
            format_money(s.total_sale_amount),
            format_money(s.total_cost),
            format_money(s.total_profit),
            format_money(s.paid_amount),
            format_money(s.debt_amount),
            get_sale_payment_types(s),
            STATUS_LABELS.get(s.status, s.status),
            s.note or "",
        ])

    if sales:
        ws.append([
            "ЖАМИ", "", "", "",
            sum(s.quantity_liters for s in sales),
            "", "", "",
            format_money(sum(s.total_sale_amount for s in sales)),
            format_money(sum(s.total_cost for s in sales)),
            format_money(sum(s.total_profit for s in sales)),
            format_money(sum(s.paid_amount for s in sales)),
            format_money(sum(s.debt_amount for s in sales)),
            "", "", "",
        ])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_sales_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 3. PURCHASES
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/purchases")
def export_purchases(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    supplier_id: int | None = Query(None),
    product_id: int | None = Query(None),
    payment_type: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Purchase).order_by(Purchase.date.desc(), Purchase.id.desc())
    if date_from:
        q = q.filter(Purchase.date >= date_from)
    if date_to:
        q = q.filter(Purchase.date <= date_to)
    if supplier_id:
        q = q.filter(Purchase.supplier_id == supplier_id)
    if product_id:
        q = q.filter(Purchase.product_id == product_id)
    if status:
        q = q.filter(Purchase.status == status)
    items = q.all()

    if payment_type:
        items = [p for p in items if any(
            pp.payment_type == payment_type and pp.status == "active" for pp in p.payments
        )]

    wb = Workbook()
    ws = wb.active
    ws.title = "Приходлар"

    headers = [
        "Сана", "Етказиб берувчи", "Маҳсулот", "Миқдор (л)",
        "1 л кирим нархи", "Умумий сумма", "Тўланган", "Қарз",
        "Тўлов тури", "Статус", "Изоҳ",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    ws.freeze_panes = "A2"

    for p in items:
        ws.append([
            str(p.date),
            p.supplier.name if p.supplier else "",
            p.product.name if p.product else "",
            p.quantity_liters,
            format_money(p.purchase_price_per_liter),
            format_money(p.total_amount),
            format_money(p.paid_amount),
            format_money(p.debt_amount),
            get_purchase_payment_types(p),
            STATUS_LABELS.get(p.status, p.status),
            p.note or "",
        ])

    if items:
        ws.append([
            "ЖАМИ", "", "",
            sum(p.quantity_liters for p in items),
            "",
            format_money(sum(p.total_amount for p in items)),
            format_money(sum(p.paid_amount for p in items)),
            format_money(sum(p.debt_amount for p in items)),
            "", "", "",
        ])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_purchases_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 4. INVENTORY
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/inventory")
def export_inventory(
    product_id: int | None = Query(None),
    supplier_id: int | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(InventoryBatch).order_by(InventoryBatch.id.desc())
    if product_id:
        q = q.filter(InventoryBatch.product_id == product_id)
    if supplier_id:
        q = q.filter(InventoryBatch.supplier_id == supplier_id)
    if status:
        q = q.filter(InventoryBatch.status == status)
    items = q.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Омбор"

    headers = [
        "Маҳсулот", "Етказиб берувчи", "Кирим нархи",
        "Бошланғич (л)", "Қолган (л)", "Қолдиқ таннархи",
        "Статус", "Сана",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    ws.freeze_panes = "A2"
    total_remaining_value = 0
    total_remaining_qty = 0

    for b in items:
        remaining_value = b.remaining_quantity_liters * b.purchase_price_per_liter
        total_remaining_value += remaining_value
        total_remaining_qty += b.remaining_quantity_liters
        ws.append([
            b.product.name if b.product else "",
            b.supplier.name if b.supplier else "",
            format_money(b.purchase_price_per_liter),
            b.initial_quantity_liters,
            b.remaining_quantity_liters,
            format_money(remaining_value),
            STATUS_LABELS.get(b.status, b.status),
            str(b.created_at.date()) if b.created_at else "",
        ])

    if items:
        ws.append([
            "ЖАМИ", "", "", "",
            total_remaining_qty,
            format_money(total_remaining_value),
            "", "",
        ])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_inventory_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 5. CUSTOMER DEBTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/customer-debts")
def export_customer_debts(
    status: str | None = Query(None),
    customer_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(CustomerDebt).order_by(CustomerDebt.id.desc())
    if status:
        q = q.filter(CustomerDebt.status == status)
    if customer_id:
        q = q.filter(CustomerDebt.customer_id == customer_id)
    items = q.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Қарздорлар"

    headers = [
        "Сана", "Мижоз", "Сотув ID",
        "Дастлабки қарз", "Тўланган", "Қолган қарз",
        "Статус", "Охирги тўлов санаси",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    ws.freeze_panes = "A2"

    for d in items:
        ws.append([
            str(d.created_at.date()) if d.created_at else "",
            d.customer.name if d.customer else "",
            d.sale_id,
            format_money(d.original_amount),
            format_money(d.paid_amount),
            format_money(d.remaining_amount),
            STATUS_LABELS.get(d.status, d.status),
            str(d.last_payment_date) if d.last_payment_date else "—",
        ])

    if items:
        ws.append([
            "ЖАМИ", "", "",
            format_money(sum(d.original_amount for d in items)),
            format_money(sum(d.paid_amount for d in items)),
            format_money(sum(d.remaining_amount for d in items)),
            "", "",
        ])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_customer_debts_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 6. SUPPLIER DEBTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/supplier-debts")
def export_supplier_debts(
    status: str | None = Query(None),
    supplier_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(SupplierDebt).order_by(SupplierDebt.id.desc())
    if status:
        q = q.filter(SupplierDebt.status == status)
    if supplier_id:
        q = q.filter(SupplierDebt.supplier_id == supplier_id)
    items = q.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Бизнинг қарзлар"

    headers = [
        "Сана", "Етказиб берувчи", "Приход ID",
        "Дастлабки қарз", "Тўланган", "Қолган қарз",
        "Статус", "Охирги тўлов санаси",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    ws.freeze_panes = "A2"

    for d in items:
        ws.append([
            str(d.created_at.date()) if d.created_at else "",
            d.supplier.name if d.supplier else "",
            d.purchase_id,
            format_money(d.original_amount),
            format_money(d.paid_amount),
            format_money(d.remaining_amount),
            STATUS_LABELS.get(d.status, d.status),
            str(d.last_payment_date) if d.last_payment_date else "—",
        ])

    if items:
        ws.append([
            "ЖАМИ", "", "",
            format_money(sum(d.original_amount for d in items)),
            format_money(sum(d.paid_amount for d in items)),
            format_money(sum(d.remaining_amount for d in items)),
            "", "",
        ])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_supplier_debts_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 7. EXPENSES
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/expenses")
def export_expenses(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category_id: int | None = Query(None),
    payment_type: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Expense).order_by(Expense.date.desc(), Expense.id.desc())
    if date_from:
        q = q.filter(Expense.date >= date_from)
    if date_to:
        q = q.filter(Expense.date <= date_to)
    if category_id:
        q = q.filter(Expense.category_id == category_id)
    if payment_type:
        q = q.filter(Expense.payment_type == payment_type)
    if status:
        q = q.filter(Expense.status == status)
    items = q.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Харажатлар"

    headers = ["Сана", "Категория", "Сумма", "Тўлов тури", "Статус", "Изоҳ"]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    for e in items:
        ws.append([
            str(e.date),
            e.category.name if e.category else "",
            format_money(e.amount),
            PAYMENT_LABELS.get(e.payment_type, e.payment_type),
            STATUS_LABELS.get(e.status, e.status),
            e.note or "",
        ])

    if items:
        ws.append(["ЖАМИ", "", format_money(sum(e.amount for e in items)), "", "", ""])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_expenses_{today_str()}.xlsx")


# ──────────────────────────────────────────────────────────────────────────────
# 8. MONEY MOVEMENTS
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/money-movements")
def export_money_movements(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    payment_type: str | None = Query(None),
    direction: str | None = Query(None),
    movement_type: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(MoneyMovement).order_by(MoneyMovement.id.desc())
    if date_from:
        q = q.filter(MoneyMovement.date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.filter(MoneyMovement.date <= datetime.combine(date_to, datetime.max.time()))
    if payment_type:
        q = q.filter(MoneyMovement.payment_type == payment_type)
    if direction:
        q = q.filter(MoneyMovement.direction == direction)
    if movement_type:
        q = q.filter(MoneyMovement.movement_type == movement_type)
    items = q.all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Пул ҳаракати"

    headers = [
        "Сана", "Ҳаракат тури", "Тўлов тури",
        "Йўналиш", "Сумма", "Боғланган модул", "Изоҳ",
    ]
    ws.append(headers)
    style_header_row(ws)
    ws.freeze_panes = "A2"

    total_in = 0
    total_out = 0

    for m in items:
        if m.direction == "income":
            total_in += m.amount
        else:
            total_out += m.amount
        ws.append([
            str(m.date.date()) if m.date else "",
            MOVEMENT_LABELS.get(m.movement_type, m.movement_type),
            PAYMENT_LABELS.get(m.payment_type, m.payment_type),
            DIRECTION_LABELS.get(m.direction, m.direction),
            format_money(m.amount),
            TABLE_LABELS.get(m.related_table, m.related_table or ""),
            m.note or "",
        ])

    if items:
        ws.append(["ЖАМИ КИРИМ", "", "", "", format_money(total_in), "", ""])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

        ws.append(["ЖАМИ ЧИҚИМ", "", "", "", format_money(total_out), "", ""])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

        ws.append(["ЖАМИ БАЛАНС", "", "", "", format_money(total_in - total_out), "", ""])
        for cell in ws[ws.max_row]:
            cell.font = SUMMARY_FONT

    auto_width(ws)
    return make_response(wb, f"natural_oil_movements_{today_str()}.xlsx")