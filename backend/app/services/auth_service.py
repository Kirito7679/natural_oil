"""Auth service — login and user management."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.auth import verify_password, create_access_token, hash_password
from app.utils.enums import UserRole


def authenticate_user(db: Session, phone: str, password: str) -> User | None:
    """Verify phone + password and return user or None."""
    user = db.query(User).filter(User.phone == phone).first()
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