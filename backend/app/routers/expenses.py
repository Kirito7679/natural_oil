"""Expenses API router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from app.schemas.expense import (
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse,
    ExpenseCreate, ExpenseResponse, ExpenseListResponse,
)
from app.services.expense_service import create_expense, cancel_expense
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


# ── Categories ──────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[ExpenseCategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(ExpenseCategory).order_by(ExpenseCategory.id).all()


@router.post("/categories", response_model=ExpenseCategoryResponse, status_code=201)
def create_category(
    data: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    existing = db.query(ExpenseCategory).filter(ExpenseCategory.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu nomdagi kategoriya mavjud.")
    cat = ExpenseCategory(name=data.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{cat_id}", response_model=ExpenseCategoryResponse)
def update_category(
    cat_id: int,
    data: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cat = db.query(ExpenseCategory).filter(ExpenseCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi.")
    if data.name is not None:
        cat.name = data.name
    if data.is_active is not None:
        cat.is_active = data.is_active
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{cat_id}/deactivate", response_model=ExpenseCategoryResponse)
def deactivate_category(
    cat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cat = db.query(ExpenseCategory).filter(ExpenseCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi.")
    cat.is_active = False
    db.commit()
    db.refresh(cat)
    return cat


# ── Expenses ────────────────────────────────────────────────────────────────

@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    category_id: int | None = None,
    payment_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Expense).order_by(Expense.id.desc())
    if status:
        query = query.filter(Expense.status == status)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if payment_type:
        query = query.filter(Expense.payment_type == payment_type)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return ExpenseListResponse(
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Xarajat topilmadi.")
    return ExpenseResponse.model_validate(expense)


@router.post("", response_model=ExpenseResponse, status_code=201)
def api_create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        expense = create_expense(db, data, user_id=current_user.id)
        return ExpenseResponse.model_validate(expense)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{expense_id}/cancel", response_model=ExpenseResponse)
def api_cancel_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        expense = cancel_expense(db, expense_id, user_id=current_user.id)
        return ExpenseResponse.model_validate(expense)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))