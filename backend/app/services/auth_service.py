"""Auth service — login and user management."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.auth import verify_password, create_access_token, hash_password
from app.utils.enums import UserRole
from app.utils.login import normalize_login


def find_user_by_login(db: Session, login: str, exclude_id: int | None = None) -> User | None:
    """Login bo'yicha foydalanuvchini topadi (bo'sh joy, +998 va harf katta-kichikligiga qaramaydi)."""
    key = normalize_login(login)
    if not key:
        return None
    for u in db.query(User).order_by(User.id).all():
        if u.id != exclude_id and normalize_login(u.phone) == key:
            return u
    return None


def authenticate_user(db: Session, phone: str, password: str) -> User | None:
    """Verify login + password and return user or None."""
    user = find_user_by_login(db, phone)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(
    db: Session,
    name: str,
    phone: str,
    password: str,
    role: UserRole = UserRole.ADMIN,
) -> User:
    """Create a new user."""
    user = User(
        name=name,
        phone=phone,
        password_hash=hash_password(password),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def generate_token(user: User) -> str:
    """Generate JWT access token for a user."""
    return create_access_token(data={"sub": str(user.id), "role": user.role})