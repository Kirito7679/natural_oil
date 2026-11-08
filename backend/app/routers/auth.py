"""Auth router — login, logout, current user."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, generate_token
from app.utils import login_guard
from app.utils.deps import get_current_user
from app.utils.login import normalize_login
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    guard_key = f"{client_ip}:{normalize_login(request.phone)}"
    if login_guard.is_locked(guard_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Кўп марта нотўғри киритилди. 10 дақиқадан кейин уриниб кўринг",
        )
    user = authenticate_user(db, request.phone, request.password)
    if user is None:
        login_guard.record_failure(guard_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Логин ёки парол нотўғри",
        )
    login_guard.reset(guard_key)
    token = generate_token(user)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user."""
    return UserResponse.model_validate(current_user)
