"""
Auth utilities: password hashing and JWT token management.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.config import settings


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Handles both bcrypt hashes AND legacy plaintext passwords from the old app.
    During migration the seed script hashes everything, but this fallback
    protects against any edge case.
    """
    try:
        if hashed_password and hashed_password.startswith("$2"):
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        # Legacy plaintext comparison
        return plain_password == hashed_password
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
