"""Foydalanuvchi yaratish yoki parolini tiklash — serverda, panelsiz.

Panelga hech kim kira olmay qolganda ham ishlaydi: to'g'ridan-to'g'ri bazaga
yozadi. Shuning uchun serverga kirish huquqi bo'lgan odamgina ishlata oladi.

Serverda ishga tushirish:

    cd /opt/naturaloil && docker compose exec -T \\
      -e 'NOP_USER_NAME=Ism Familiya' \\
      -e NOP_USER_LOGIN=900350151 \\
      -e 'NOP_USER_PASSWORD=...' \\
      -e NOP_USER_ROLE=dev \\
      api python -m app.create_user

Shunday login allaqachon bo'lsa — ismi, roli va paroli yangilanadi
(normalize_login: "+998900350151", "90 035 01 51" va "900350151" — bitta login).
NOP_USER_ROLE berilmasa, dev yaratiladi.
"""
import os
import sys

from app.database import SessionLocal, create_tables
from app.models.user import User
from app.services.auth_service import find_user_by_login
from app.utils.auth import hash_password
from app.utils.enums import UserRole

MIN_PASSWORD_LEN = 6


def main() -> int:
    name = (os.getenv("NOP_USER_NAME") or "").strip()
    login = (os.getenv("NOP_USER_LOGIN") or "").strip()
    password = os.getenv("NOP_USER_PASSWORD") or ""
    role = (os.getenv("NOP_USER_ROLE") or UserRole.DEV.value).strip()

    missing = [k for k, v in (("NOP_USER_NAME", name), ("NOP_USER_LOGIN", login),
                              ("NOP_USER_PASSWORD", password)) if not v]
    if missing:
        print("Kerakli o'zgaruvchilar berilmagan: " + ", ".join(missing), file=sys.stderr)
        return 2
    if len(password) < MIN_PASSWORD_LEN:
        print(f"Parol kamida {MIN_PASSWORD_LEN} ta belgidan iborat bo'lishi kerak", file=sys.stderr)
        return 2
    allowed = [r.value for r in UserRole]
    if role not in allowed:
        print(f"Noma'lum rol: {role}. Mumkin: {', '.join(allowed)}", file=sys.stderr)
        return 2

    create_tables()
    db = SessionLocal()
    try:
        user = find_user_by_login(db, login)
        if user is None:
            user = User(name=name, phone=login, role=role,
                        password_hash=hash_password(password), is_active=True)
            db.add(user)
            action = "yaratildi"
        else:
            user.name = name
            user.role = role
            user.is_active = True
            user.password_hash = hash_password(password)
            action = "yangilandi"
        db.commit()
        db.refresh(user)
        print(f"{action}: #{user.id}  {user.name}  /  {user.phone}  /  {user.role}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
