"""Balance router — view balances, set initial, adjust, money movements."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.money_movement import MoneyMovement
from app.schemas.balance import BalanceResponse, InitialBalanceRequest, BalanceAdjustmentRequest, AddInitialBalanceRequest
from app.schemas.money_movement import MoneyMovementResponse, MoneyMovementListResponse
from app.services.balance_service import get_balance, set_initial_balance, adjust_balance, update_balance
from app.utils.enums import MovementType, MovementDirection
from app.utils.deps import get_current_user, require_admin

def _parse_date(value: str | None):
    from datetime import date as _date
    try:
        return _date.fromisoformat(value) if value else None
    except ValueError:
        return None


router = APIRouter(prefix="/api/balance", tags=["Balance"])


@router.get("", response_model=BalanceResponse)
def view_balance(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """View current balance — cash, bank transfer, and total."""
    return get_balance(db)


@router.post("/initial", response_model=BalanceResponse)
def set_initial(
    request: InitialBalanceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Set initial balance. Admin only."""
    return set_initial_balance(
        db,
        cash_amount=request.cash_amount,
        bank_transfer_amount=request.bank_transfer_amount,
        user_id=admin.id,
    )


@router.post("/add-initial", response_model=BalanceResponse)
def add_initial_balance(
    request: AddInitialBalanceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Add existing money (O'zida bor pul) to selected balance. Admin only."""
    # We use update_balance helper directly
    try:
        update_balance(
            db=db,
            payment_type=request.payment_type,
            amount=request.amount,
            direction=MovementDirection.INCOME,
            movement_type=MovementType.INITIAL_BALANCE,
            note=request.note or "Бошланғич баланс",
            user_id=admin.id,
            auto_commit=True,
            on_date=_parse_date(request.date),
        )
        return get_balance(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/adjust", response_model=BalanceResponse)
def adjust(
    request: BalanceAdjustmentRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Adjust balance. Admin only. Positive = add, negative = subtract."""
    try:
        return adjust_balance(
            db,
            payment_type=request.payment_type,
            amount=request.amount,
            note=request.note,
            user_id=admin.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


from app.services.formatting_service import get_rich_description

@router.get("/movements", response_model=MoneyMovementListResponse)
def list_money_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """List money movement history, newest first."""
    query = db.query(MoneyMovement).order_by(MoneyMovement.id.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    res_items = []
    for m in items:
        m_dict = {k: getattr(m, k) for k in m.__table__.columns.keys()}
        m_dict["note"] = get_rich_description(db, m)
        res_items.append(MoneyMovementResponse.model_validate(m_dict))

    return MoneyMovementListResponse(
        items=res_items,
        total=total,
    )


# Qo'lda kiritilgan pul harakatini bekor qilish. Sotuv/prixod/xarajat/qarz
# to'lovidan kelgan harakat bu yerdan bekor qilinmaydi: uning o'rniga o'sha
# hujjatning o'zi bekor qilinadi, aks holda balans hujjatdan ajralib qoladi.
_CANCELLABLE_MOVEMENTS = {
    MovementType.INITIAL_BALANCE.value,
    MovementType.BALANCE_ADJUSTMENT.value,
}


@router.patch("/movements/{movement_id}/cancel", response_model=BalanceResponse)
def cancel_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Noto'g'ri kiritilgan pul harakatini bekor qiladi.

    Yozuvning o'zi o'chmaydi — teskari yo'nalishda qarshi harakat yoziladi,
    shuning uchun tarixda nima bo'lgani ko'rinib turadi.
    """
    movement = db.query(MoneyMovement).filter(MoneyMovement.id == movement_id).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Пул ҳаракати топилмади")

    if movement.movement_type not in _CANCELLABLE_MOVEMENTS:
        raise HTTPException(
            status_code=400,
            detail="Бу ҳаракат сотув, приход, харажат ёки қарз тўловидан келиб чиққан. "
                   "Уни бекор қилиш учун ўша ҳужжатнинг ўзини бекор қилинг.",
        )

    already = (
        db.query(MoneyMovement)
        .filter(
            MoneyMovement.movement_type == MovementType.CANCELLATION.value,
            MoneyMovement.related_table == "money_movements",
            MoneyMovement.related_id == movement_id,
        )
        .first()
    )
    if already:
        raise HTTPException(status_code=400, detail="Бу ҳаракат аллақачон бекор қилинган")

    from app.utils.enums import PaymentType as _PT
    opposite = (
        MovementDirection.OUTGOING
        if movement.direction == MovementDirection.INCOME.value
        else MovementDirection.INCOME
    )
    try:
        update_balance(
            db=db,
            payment_type=_PT(movement.payment_type),
            amount=movement.amount,
            direction=opposite,
            movement_type=MovementType.CANCELLATION,
            related_table="money_movements",
            related_id=movement.id,
            note=f"Бекор қилинди: {movement.note or movement.movement_type}",
            user_id=admin.id,
            auto_commit=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return get_balance(db)
