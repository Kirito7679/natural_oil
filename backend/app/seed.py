"""Seed script — creates default data on first startup.

Creates:
- Admin user
- Default products (AI-80, AI-91, AI-92, AI-95, Diesel, Other)
- Default expense categories
- Balance accounts (cash + bank_transfer)
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.product import Product
from app.models.expense import ExpenseCategory
from app.models.balance import BalanceAccount
from app.utils.auth import hash_password
from app.utils.enums import PaymentType, UserRole
from app.config import settings


DEFAULT_PRODUCTS = [
    "AI-80",
    "AI-91",
    "AI-92",
    "AI-95",
    "Dizel",
    "Boshqa",
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Arenda",
    "Oylik",
    "Transport",
    "Kommunalka",
    "Remont",
    "Boshqa",
]

# Only cash and bank_transfer — NO card
BALANCE_ACCOUNT_TYPES = [
    PaymentType.CASH.value,
    PaymentType.BANK_TRANSFER.value,
]


def seed_database(db: Session) -> None:
    """Populate the database with initial data if empty."""

    # 1. Admin user
    existing_admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
    if existing_admin is None:
        admin = User(
            name=settings.ADMIN_NAME,
            phone=settings.ADMIN_PHONE,
            role=UserRole.ADMIN.value,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
        )
        db.add(admin)
        print(f"[SEED] Admin yaratildi: {settings.ADMIN_PHONE}")

    # 2. Default products
    for pname in DEFAULT_PRODUCTS:
        exists = db.query(Product).filter(Product.name == pname).first()
        if exists is None:
            db.add(Product(name=pname, unit="liter"))
    print(f"[SEED] Mahsulotlar tekshirildi: {len(DEFAULT_PRODUCTS)} ta")

    # 3. Default expense categories
    for cname in DEFAULT_EXPENSE_CATEGORIES:
        exists = db.query(ExpenseCategory).filter(ExpenseCategory.name == cname).first()
        if exists is None:
            db.add(ExpenseCategory(name=cname))
    print(f"[SEED] Xarajat kategoriyalari tekshirildi: {len(DEFAULT_EXPENSE_CATEGORIES)} ta")

    # 4. Balance accounts — only cash and bank_transfer
    for btype in BALANCE_ACCOUNT_TYPES:
        exists = db.query(BalanceAccount).filter(BalanceAccount.type == btype).first()
        if exists is None:
            db.add(BalanceAccount(type=btype, current_balance=0.0))
    print("[SEED] Balans hisoblar tekshirildi: Naqd va Perechisleniya")

    db.commit()
    print("[SEED] Ma'lumotlar bazasi tayyor.")
