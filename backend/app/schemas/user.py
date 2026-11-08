"""Pydantic schemas for user & auth."""

from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator

from app.utils.enums import UserRole


class UserBase(BaseModel):
    name: str
    phone: str
    role: UserRole = UserRole.ADMIN


class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    confirm_password: str
    is_active: bool = True
    role: UserRole = UserRole.ADMIN

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Исм бўш бўлиши мумкин эмас")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Логин бўш бўлиши мумкин эмас")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Парол камида 6 та белгидан иборат бўлиши керак.")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Пароллар мос эмас.")
        return self


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Янги парол камида 6 та белгидан иборат бўлиши керак.")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Пароллар мос эмас.")
        return self


class PasswordReset(BaseModel):
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Янги парол камида 6 та белгидан иборат бўлиши керак.")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Пароллар мос эмас.")
        return self


class UserResponse(BaseModel):
    id: int
    name: str
    phone: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse