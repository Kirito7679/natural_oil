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
            note=request.note or "Boshlang'ich balans",
            user_id=admin.id,
            auto_commit=True,
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
    return MoneyMovementListResponse(
        items=[MoneyMovementResponse.model_validate(m) for m in items],
        total=total,
    )
