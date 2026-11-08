"""Admin router — clear all data except users."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.auth import verify_password
from app.utils.deps import get_current_user
from app.utils.enums import FULL_ACCESS_ROLES

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class ClearDataRequest(BaseModel):
    password: str
    confirm_text: str


# Tartib MUHIM — bog'liq jadvallarni avval o'chiramiz, keyin asosiylarini.
# Foreign key'lar yo'nalishini hisobga olib yozilgan.
DELETE_ORDER = [
    # Eng pastki bog'liqliklar (boshqa jadvallarga referens)
    "audit_logs",
    "money_movements",
    "debt_payments",
    "sale_payments",
    "purchase_payments",
    # Qarzlar (sales/purchases'ga bog'langan)
    "customer_debts",
    "supplier_debts",
    # Asosiy tranzaksiyalar
    "sales",
    "purchases",
    "expenses",
    # Inventory (purchases'ga bog'langan bo'lishi mumkin, shuning uchun keyin)
    "inventory_batches",
    # Bog'liqlik manbalari
    "expense_categories",
    "partners",
    "products",
]


@router.post("/clear-data")
def clear_data(
    payload: ClearDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tizimni to'liq tozalash. Faqat foydalanuvchilar (login) saqlanadi."""

    # Faqat to'liq huquqli rollar (direktor yoki dev)
    if current_user.role not in FULL_ACCESS_ROLES:
        raise HTTPException(status_code=403, detail="Фақат директор бажара олади")

    # Parolni tekshirish
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Парол нотўғри")

    # Tasdiqlash matnini tekshirish
    if payload.confirm_text.strip().upper() not in ("TOZALASH", "ТОЗАЛАШ"):
        raise HTTPException(status_code=400, detail="Тасдиқлаш матни нотўғри. 'ТОЗАЛАШ' деб ёзинг.")

    deleted_counts = {}

    try:
        # SQLite uchun foreign key constraint vaqtincha o'chiramiz
        db.execute(text("PRAGMA foreign_keys = OFF"))

        # Har bir jadvalni tartib bo'yicha o'chiramiz
        for table_name in DELETE_ORDER:
            try:
                result = db.execute(text(f"DELETE FROM {table_name}"))
                deleted_counts[table_name] = result.rowcount or 0
            except Exception as e:
                # Jadval mavjud bo'lmasa o'tkazib yuborish (xato bermaslik uchun)
                deleted_counts[table_name] = f"skipped: {str(e)[:50]}"

        # Balanslarni 0 ga tushirish (qatorlar saqlanadi, faqat 0 bo'ladi)
        db.execute(text("UPDATE balance_accounts SET current_balance = 0"))
        deleted_counts["balances_reset"] = "ok"

        # Foreign key'larni qayta yoqamiz
        db.execute(text("PRAGMA foreign_keys = ON"))

        db.commit()
    except Exception as e:
        db.rollback()
        # Foreign key'lar yoqilgan ekanligiga ishonch hosil qilamiz
        try:
            db.execute(text("PRAGMA foreign_keys = ON"))
            db.commit()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Тозалашда хатолик: {str(e)}")

    return {
        "ok": True,
        "message": "Тизим муваффақиятли тозаланди",
        "deleted": deleted_counts,
    }