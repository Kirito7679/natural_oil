"""Application settings loaded from environment / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./natural_oil.db"

    # JWT
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Admin seed
    # Asosiy foydalanuvchi (birinchi ishga tushishda yaratiladi; parolni keyin tizimda o'zi o'zgartiradi).
    # Eski ADMIN_* kalitlari endi ishlatilmaydi.
    MAIN_USER_NAME: str = "Хумоюн"
    MAIN_USER_LOGIN: str = "95 810 06 00"
    MAIN_USER_PASSWORD: str = "1234567"

    # CORS — production domain; override in local .env for dev
    FRONTEND_URL: str = "https://naturaloilerp.uz"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()