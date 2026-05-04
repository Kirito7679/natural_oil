"""User management router — admin access management (Phase 9)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    PasswordChange, PasswordReset,
)
from app.utils.auth import hash_password, verify_password
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


def count_active_admins(db: Session) -> int:
    return db.query(User).filter(User.is_active == True).count()


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Barcha foydalanuvchilar ro'yxati."""
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Yangi admin foydalanuvchi yaratish."""
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Parollar mos emas.")

    existing = db.query(User).filter(User.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu login allaqachon mavjud.")

    user = User(
        name=data.name,
        phone=data.phone,
        role="admin",
        password_hash=hash_password(data.password),
        is_active=data.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Foydalanuvchi ma'lumotlarini yangilash (ism / login / faollik)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")

    # Check duplicate phone if changing
    if data.phone is not None and data.phone != user.phone:
        existing = db.query(User).filter(User.phone == data.phone, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu login allaqachon mavjud.")
        user.phone = data.phone

    if data.name is not None:
        user.name = data.name

    # Deactivation safety check
    if data.is_active is not None and data.is_active == False and user.is_active == True:
        # Check if this is the last active admin
        if count_active_admins(db) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Oxirgi faol adminni o'chirib bo'lmaydi.",
            )
        user.is_active = False
    elif data.is_active is not None and data.is_active == True:
        user.is_active = True

    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", response_model=UserResponse)
def reset_user_password(
    user_id: int,
    data: PasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Boshqa foydalanuvchining parolini almashtirish."""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Parollar mos emas.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/change-password", response_model=UserResponse)
def change_own_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """O'z parolini almashtirish."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Joriy parol noto'g'ri.")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Parollar mos emas.")

    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user