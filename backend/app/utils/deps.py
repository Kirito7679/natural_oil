"""FastAPI dependencies — DB session, current user, role checks."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.auth import decode_access_token
from app.utils.enums import UserRole

security = HTTPBearer()


# Investor faqat ko'radi. Unga ruxsat etilgan yagona "yozish" amallari:
INVESTOR_WRITE_ALLOWED = ("/api/auth/", "/api/users/me/change-password")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate user from JWT token."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен яроқсиз ёки муддати тугаган",
        )
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен яроқсиз",
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Фойдаланувчи топилмади",
        )
    if (
        user.role == UserRole.INVESTOR.value
        and request.method not in ("GET", "HEAD", "OPTIONS")
        and not request.url.path.startswith(INVESTOR_WRITE_ALLOWED)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Инвестор ҳисоби фақат кўриш учун. Ўзгартириш мумкин эмас.",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Only admin can access this endpoint."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Фақат директор учун рухсат берилган",
        )
    return current_user
