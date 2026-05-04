"""Balance service — view, set initial, adjust, and modify balances.

Balance accounts:
- cash (Naqd)
- bank_transfer (Perechisleniya)

NO card balance account.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.balance import BalanceAccount
from app.models.money_movement import MoneyMovement
from app.utils.enums import PaymentType, MovementType, MovementDirection


def get_or_create_balance_accounts(db: Session) -> dict[str, BalanceAccount]:
    """Ensure both balance accounts exist, return as dict."""
    accounts = {}
    for ptype in [PaymentType.CASH, PaymentType.BANK_TRANSFER]:
        acc = db.query(BalanceAccount).filter(BalanceAccount.type == ptype.value).first()
        if acc is None:
            acc = BalanceAccount(type=ptype.value, current_balance=0.0)
            db.add(acc)
            db.commit()
            db.refresh(acc)
        accounts[ptype.value] = acc
    return accounts


def get_balance(db: Session) -> dict:
    """Return current balances."""
    accounts = get_or_create_balance_accounts(db)
    cash = accounts[PaymentType.CASH.value].current_balance
    bank = accounts[PaymentType.BANK_TRANSFER.value].current_balance
    return {
        "cash_balance": cash,
        "bank_transfer_balance": bank,
        "total_balance": cash + bank,
    }


def set_initial_balance(
    db: Session,
    cash_amount: float,
    bank_transfer_amount: float,
    user_id: int | None = None,
) -> dict:
    """Set initial balance for both accounts. Records money movements."""
    accounts = get_or_create_balance_accounts(db)
    now = datetime.now(timezone.utc)

    # Set cash
    cash_acc = accounts[PaymentType.CASH.value]
    old_cash = cash_acc.current_balance
    cash_acc.current_balance = cash_amount

    if cash_amount > 0:
        db.add(MoneyMovement(
            date=now,
            movement_type=MovementType.INITIAL_BALANCE.value,
            payment_type=PaymentType.CASH.value,
            direction=MovementDirection.INCOME.value,
            amount=cash_amount,
            related_table="balance_accounts",
            related_id=cash_acc.id,
            note=f"Boshlang'ich naqd balans: {cash_amount:,.0f} UZS",
            created_by=user_id,
        ))

    # Set bank transfer
    bank_acc = accounts[PaymentType.BANK_TRANSFER.value]
    old_bank = bank_acc.current_balance
    bank_acc.current_balance = bank_transfer_amount

    if bank_transfer_amount > 0:
        db.add(MoneyMovement(
            date=now,
            movement_type=MovementType.INITIAL_BALANCE.value,
            payment_type=PaymentType.BANK_TRANSFER.value,
            direction=MovementDirection.INCOME.value,
            amount=bank_transfer_amount,
            related_table="balance_accounts",
            related_id=bank_acc.id,
            note=f"Boshlang'ich perechisleniya balans: {bank_transfer_amount:,.0f} UZS",
            created_by=user_id,
        ))

    db.commit()
    return get_balance(db)


def adjust_balance(
    db: Session,
    payment_type: PaymentType,
    amount: float,
    note: str = "",
    user_id: int | None = None,
) -> dict:
    """Admin balance adjustment. Positive = add, negative = subtract."""
    accounts = get_or_create_balance_accounts(db)
    acc = accounts[payment_type.value]
    now = datetime.now(timezone.utc)

    # Determine direction
    if amount >= 0:
        direction = MovementDirection.INCOME.value
    else:
        direction = MovementDirection.OUTGOING.value
        # Check if balance is sufficient for negative adjustment
        if acc.current_balance + amount < 0:
            raise ValueError(
                f"Balansda yetarli mablag' yo'q. "
                f"Joriy balans: {acc.current_balance:,.0f}, "
                f"Tuzatish: {amount:,.0f}"
            )

    acc.current_balance += amount

    db.add(MoneyMovement(
        date=now,
        movement_type=MovementType.BALANCE_ADJUSTMENT.value,
        payment_type=payment_type.value,
        direction=direction,
        amount=abs(amount),
        related_table="balance_accounts",
        related_id=acc.id,
        note=note or f"Balans tuzatish: {amount:,.0f} UZS",
        created_by=user_id,
    ))

    db.commit()
    return get_balance(db)


def update_balance(
    db: Session,
    payment_type: PaymentType,
    amount: float,
    direction: MovementDirection,
    movement_type: MovementType,
    related_table: str | None = None,
    related_id: int | None = None,
    note: str = "",
    user_id: int | None = None,
    auto_commit: bool = False,
) -> None:
    """Internal helper: update a balance account and record a money movement.

    Used by purchase, sale, expense, and debt payment services.
    Does NOT commit — caller must commit the transaction.
    """
    accounts = get_or_create_balance_accounts(db)
    acc = accounts[payment_type.value]
    now = datetime.now(timezone.utc)

    if direction == MovementDirection.OUTGOING:
        if acc.current_balance < amount:
            type_label = "Naqd" if payment_type == PaymentType.CASH else "Perechisleniya"
            raise ValueError(
                f"{type_label} balansda yetarli mablag' yo'q. "
                f"Joriy balans: {acc.current_balance:,.0f}, "
                f"Kerakli summa: {amount:,.0f}"
            )
        acc.current_balance -= amount
    else:
        acc.current_balance += amount

    db.add(MoneyMovement(
        date=now,
        movement_type=movement_type.value,
        payment_type=payment_type.value,
        direction=direction.value,
        amount=amount,
        related_table=related_table,
        related_id=related_id,
        note=note,
        created_by=user_id,
    ))

    if auto_commit:
        db.commit()
