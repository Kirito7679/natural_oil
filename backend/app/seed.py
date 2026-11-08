"""Seed script — creates default data on first startup.

Creates:
- Asosiy foydalanuvchi (Хумоюн)
- Mahsulotlar YARATILMAYDI — foydalanuvchi o'zi kiritadi
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


DEFAULT_EXPENSE_CATEGORIES = [
    "Ёқилғи ташиш (логистика)",
    "Ҳайдовчи ва ишчилар ойлиги",
    "Ижара (омбор, офис)",
    "Солиқ ва йиғимлар",
    "Банк хизматлари ва комиссия",
    "Коммунал тўловлар",
    "Таъмирлаш ва техник хизмат",
    "Алоқа ва интернет",
    "Офис ва хўжалик харажатлари",
    "Бошқа",
]

# Eski standart ro'yxat (lotin va kirill). Ishlatilmagan bo'lsa o'chiriladi,
# ishlatilgan bo'lsa nomi kirillga o'giriladi.
LEGACY_EXPENSE_CATEGORIES = {
    "Arenda": "Ижара (омбор, офис)", "Аренда": "Ижара (омбор, офис)",
    "Oylik": "Ҳайдовчи ва ишчилар ойлиги", "Ойлик": "Ҳайдовчи ва ишчилар ойлиги",
    "Transport": "Ёқилғи ташиш (логистика)", "Транспорт": "Ёқилғи ташиш (логистика)",
    "Kommunalka": "Коммунал тўловлар", "Коммуналка": "Коммунал тўловлар",
    "Remont": "Таъмирлаш ва техник хизмат", "Ремонт": "Таъмирлаш ва техник хизмат",
    "Boshqa": "Бошқа",
}

LEGACY_PRODUCT_NAMES = {"Dizel": "Дизел", "Boshqa": "Бошқа"}

# Only cash and bank_transfer — NO card
BALANCE_ACCOUNT_TYPES = [
    PaymentType.CASH.value,
    PaymentType.BANK_TRANSFER.value,
]


def seed_database(db: Session) -> None:
    """Populate the database with initial data if empty."""

    # 1. Asosiy foydalanuvchi (bazada hech kim bo'lmasa)
    if db.query(User).count() == 0:
        db.add(User(
            name=settings.MAIN_USER_NAME,
            phone=settings.MAIN_USER_LOGIN,
            role=UserRole.ADMIN.value,
            password_hash=hash_password(settings.MAIN_USER_PASSWORD),
        ))
        db.flush()
        print(f"[SEED] Asosiy foydalanuvchi yaratildi: {settings.MAIN_USER_LOGIN}")

    # 2. Bir martalik tozalash: bitta asosiy foydalanuvchi, standart mahsulotlarsiz
    _one_time_main_user_cleanup(db)

    # 3. Default expense categories
    _sync_expense_categories(db)
    _rename_legacy_products(db)
    _close_ghost_debts(db)
    print(f"[SEED] Xarajat kategoriyalari tekshirildi: {len(DEFAULT_EXPENSE_CATEGORIES)} ta")

    # 4. Balance accounts — only cash and bank_transfer
    for btype in BALANCE_ACCOUNT_TYPES:
        exists = db.query(BalanceAccount).filter(BalanceAccount.type == btype).first()
        if exists is None:
            db.add(BalanceAccount(type=btype, current_balance=0.0))
    print("[SEED] Balans hisoblar tekshirildi: Naqd va Perechisleniya")

    db.commit()
    print("[SEED] Ma'lumotlar bazasi tayyor.")


def _sync_expense_categories(db: Session) -> None:
    """Xarajat kategoriyalarini yangi ro'yxatga moslaydi, ma'lumotni yo'qotmasdan."""
    from app.models.expense import Expense

    # Yangi ro'yxat avval o'rnatilganmi? (legacy nomni o'zgartirishdan OLDIN tekshiramiz)
    has_new = db.query(ExpenseCategory).filter(ExpenseCategory.name.in_(DEFAULT_EXPENSE_CATEGORIES)).count() > 0

    for old_name, new_name in LEGACY_EXPENSE_CATEGORIES.items():
        old = db.query(ExpenseCategory).filter(ExpenseCategory.name == old_name).first()
        if old is None:
            continue
        used = db.query(Expense).filter(Expense.category_id == old.id).count()
        target = db.query(ExpenseCategory).filter(ExpenseCategory.name == new_name).first()
        if used == 0:
            db.delete(old)
        elif target is None:
            old.name = new_name
        else:
            # Ikkalasi ham bor: xarajatlarni yangi kategoriyaga ko'chiramiz
            db.query(Expense).filter(Expense.category_id == old.id).update({Expense.category_id: target.id})
            db.delete(old)
        db.flush()

    # Yangi ro'yxat faqat bir marta qo'shiladi (keyin foydalanuvchi o'zi boshqaradi)
    if not has_new:
        for cname in DEFAULT_EXPENSE_CATEGORIES:
            if db.query(ExpenseCategory).filter(ExpenseCategory.name == cname).first() is None:
                db.add(ExpenseCategory(name=cname))
    db.flush()


def _rename_legacy_products(db: Session) -> None:
    """Eski lotin nomli standart mahsulotlarni kirillga o'giradi."""
    for old_name, new_name in LEGACY_PRODUCT_NAMES.items():
        old = db.query(Product).filter(Product.name == old_name).first()
        if old and db.query(Product).filter(Product.name == new_name).first() is None:
            old.name = new_name
    db.flush()


def _close_ghost_debts(db: Session) -> None:
    """Kasr yaxlitlash sababli qolib ketgan 0 so'mlik "faol" qarzlarni yopadi."""
    from app.models.debt import CustomerDebt, SupplierDebt
    for model in (CustomerDebt, SupplierDebt):
        for d in db.query(model).filter(model.status == "active", model.remaining_amount < 0.01).all():
            d.remaining_amount = 0.0
            d.status = "closed"
    db.flush()


# ── Bir martalik migratsiya ──────────────────────────────────────────────────
MIGRATION_KEY = "main_user_cleanup_v1"


def _meta_done(db: Session, key: str) -> bool:
    from sqlalchemy import text
    db.execute(text("CREATE TABLE IF NOT EXISTS app_meta (key VARCHAR(100) PRIMARY KEY, value TEXT)"))
    return db.execute(text("SELECT 1 FROM app_meta WHERE key = :k"), {"k": key}).first() is not None


def _meta_mark(db: Session, key: str) -> None:
    from datetime import datetime
    from sqlalchemy import text
    db.execute(text("INSERT INTO app_meta (key, value) VALUES (:k, :v)"), {"k": key, "v": datetime.now().isoformat()})


def _backup_sqlite() -> None:
    """Migratsiyadan oldin bazaning nusxasini saqlaydi (faqat SQLite)."""
    import shutil
    from datetime import datetime
    from app.database import engine
    path = engine.url.database
    if engine.url.get_backend_name() != "sqlite" or not path or path == ":memory:":
        return
    import os
    if os.path.exists(path):
        dst = f"{path}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(path, dst)
        print(f"[MIGRATION] Zaxira nusxa: {dst}")


def _one_time_main_user_cleanup(db: Session) -> None:
    """Bitta asosiy foydalanuvchi qoldiradi va ishlatilmagan standart mahsulotlarni o'chiradi.

    - Asosiy foydalanuvchi: ismi, logini va paroli settings'dan olinadi (Хумоюн / 95 810 06 00 / 1234567).
    - Boshqa foydalanuvchilar o'chiriladi; ular yozgan yozuvlar asosiy foydalanuvchiga o'tkaziladi.
    - Hech qayerda ishlatilmagan mahsulotlar o'chiriladi (foydalanuvchi o'zi kiritadi).
    Faqat bir marta ishlaydi — keyin parol va foydalanuvchilarni o'zi boshqaradi.
    """
    from sqlalchemy import text
    from app.utils.login import normalize_login

    if _meta_done(db, MIGRATION_KEY):
        return
    _backup_sqlite()

    users = db.query(User).order_by(User.id).all()
    key = normalize_login(settings.MAIN_USER_LOGIN)
    main = next((u for u in users if normalize_login(u.phone) == key), None) \
        or next((u for u in users if u.role == UserRole.ADMIN.value), None) \
        or (users[0] if users else None)
    if main is None:
        main = User(name=settings.MAIN_USER_NAME, phone=settings.MAIN_USER_LOGIN, role=UserRole.ADMIN.value,
                    password_hash=hash_password(settings.MAIN_USER_PASSWORD))
        db.add(main)
        db.flush()
    others = [u.id for u in users if u.id != main.id]
    if others:
        refs = [("sales", "created_by"), ("purchases", "created_by"), ("expenses", "created_by"),
                ("money_movements", "created_by"), ("debt_payments", "created_by"), ("audit_logs", "user_id")]
        for table, col in refs:
            db.execute(text(f"UPDATE {table} SET {col} = :m WHERE {col} IN ({','.join(str(i) for i in others)})"), {"m": main.id})
        db.query(User).filter(User.id.in_(others)).delete(synchronize_session=False)
        print(f"[MIGRATION] {len(others)} ta boshqa foydalanuvchi o'chirildi")

    # Boshqalar o'chirilgandan keyin asosiy foydalanuvchi ma'lumotlarini yangilaymiz
    main.name = settings.MAIN_USER_NAME
    main.phone = settings.MAIN_USER_LOGIN
    main.role = UserRole.ADMIN.value
    main.is_active = True
    main.password_hash = hash_password(settings.MAIN_USER_PASSWORD)
    db.flush()

    used = set()
    for table in ("purchases", "sales", "inventory_batches"):
        used |= {r[0] for r in db.execute(text(f"SELECT DISTINCT product_id FROM {table}")).fetchall()}
    removed = 0
    for p in db.query(Product).all():
        if p.id not in used:
            db.delete(p)
            removed += 1
    db.flush()
    if removed:
        print(f"[MIGRATION] {removed} ta ishlatilmagan mahsulot o'chirildi")

    _meta_mark(db, MIGRATION_KEY)
    db.flush()
