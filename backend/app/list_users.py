"""Bazadagi foydalanuvchilar ro'yxati — serverda, panelsiz.

Parollar ko'rsatilmaydi va ko'rsatib bo'lmaydi: bazada faqat ularning hash'i
turadi. Parolni unutgan bo'lsa — app.create_user bilan yangisini qo'ying.

Serverda ishga tushirish:

    cd /opt/naturaloil && docker compose exec -T api python -m app.list_users
"""
from app.database import SessionLocal
from app.models.user import User
from app.utils.login import normalize_login


def main() -> int:
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        if not users:
            print("Bazada foydalanuvchi yo'q")
            return 0
        print(f"{'ID':>3}  {'ISM':<24} {'LOGIN':<16} {'SOLISHTIRISH':<12} {'ROL':<9} HOLAT")
        for u in users:
            holat = "faol" if u.is_active else "nofaol"
            print(f"{u.id:>3}  {u.name:<24} {u.phone:<16} {normalize_login(u.phone):<12} {u.role:<9} {holat}")
        print(f"\nJami: {len(users)}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
