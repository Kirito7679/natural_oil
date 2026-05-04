"""JWT token and password hashing utilities — using hashlib (no bcrypt)."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings


def hash_password(password: str) -> str:
    """SHA256 + salt hashing."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${pw_hash}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password — supports both new (salt$hash) and old bcrypt format."""
    try:
        # New format: salt$hash
        if "$" in hashed and not hashed.startswith("$2"):
            salt, pw_hash = hashed.split("$", 1)
            return hashlib.sha256((salt + plain).encode()).hexdigest() == pw_hash
        # Old bcrypt format — try bcrypt
        try:
            import bcrypt
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except Exception:
            return False
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None