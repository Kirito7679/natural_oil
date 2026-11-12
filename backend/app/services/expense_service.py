"""Expense business logic.

Creating expense → decreases balance + creates money movement.
Cancelling expense → restores balance + creates cancellation movement.
Only cash and bank_transfer. NO card.
"""

from sqlalchemy.orm import Session

from app.models.expense import Expense, ExpenseCategory
from app.schemas.expense import ExpenseCreate
from app.services.balance_service import update_balance
from app.utils.enums import PaymentType, MovementType, MovementDirection


def create_expense(
    db: Session, data: ExpenseCreate, user_id: int | None = None,
    auto_commit: bool = True,
) -> Expense:
    """Create expense and decrease balance."""

    # Validate category
    category = db.query(ExpenseCategory).filter(
        ExpenseCategory.id == data.category_id,
        ExpenseCategory.is_active == True,
    ).first()
    if not category:
        raise ValueError("Категория топилмади ёки фаол эмас.")

    # Create expense record
    expense = Expense(
        date=data.date,
        category_id=data.category_id,
        amount=data.amount,
        payment_type=data.payment_type.value,
        note=data.note,
        status="active",
        created_by=user_id,
    )
    db.add(expense)
    db.flush()

    # Decrease balance (will raise ValueError if insufficient)
    update_balance(
        db=db,
        payment_type=data.payment_type,
        amount=data.amount,
        direction=MovementDirection.OUTGOING,
        movement_type=MovementType.EXPENSE,
        related_table="expenses",
        related_id=expense.id,
        note=f"Харажат: {category.name}" + (f". {data.note}" if data.note else ""),
        user_id=user_id,
        auto_commit=False,
            on_date=data.date,
    )

    if auto_commit:
        db.commit()
        db.refresh(expense)
    return expense


def cancel_expense(
    db: Session, expense_id: int, user_id: int | None = None,
    auto_commit: bool = True,
) -> Expense:
    """Cancel expense and restore balance."""

    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise ValueError("Харажат топилмади.")
    if expense.status == "cancelled":
        raise ValueError("Бу харажат аллақачон бекор қилинган.")

    # Mark as cancelled
    expense.status = "cancelled"

    # Restore balance
    from app.utils.enums import PaymentType as PT
    payment_type = PT(expense.payment_type)

    update_balance(
        db=db,
        payment_type=payment_type,
        amount=expense.amount,
        direction=MovementDirection.INCOME,
        movement_type=MovementType.EXPENSE,
        related_table="expenses",
        related_id=expense.id,
        note=f"Харажат бекор қилинди. ID: {expense.id}",
        user_id=user_id,
        auto_commit=False,
    )

    if auto_commit:
        db.commit()
        db.refresh(expense)
    return expense

def edit_expense(
    db: Session, expense_id: int, data: ExpenseCreate, user_id: int | None = None
) -> Expense:
    """Xarajatni to'g'rilash: eskisini bekor qilib, yangisini yozadi. Bitta tranzaksiyada."""
    try:
        cancel_expense(db, expense_id, user_id=user_id, auto_commit=False)
        new_expense = create_expense(db, data, user_id=user_id, auto_commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_expense)
    return new_expense
