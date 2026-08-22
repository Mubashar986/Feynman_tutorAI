from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from pydantic import ValidationError

from backend.app.core.config import settings
from backend.app.auth.models import TokenPayload


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt with adaptive salt cost (rounds=12).
    Resistant against GPU/ASIC brute-force attacks (OWASP standard).
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored bcrypt hash using constant-time comparison.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generates a signed, stateless RFC 7519 HMAC-SHA256 JSON Web Token (JWT).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decodes and cryptographically verifies a JWT token.
    Returns TokenPayload on success, None if expired or invalid.
    """
    try:
        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return TokenPayload(
            sub=decoded.get("sub", ""),
            role=decoded.get("role", ""),
            exp=decoded.get("exp", 0),
        )
    except (jwt.PyJWTError, ValidationError):
        return None
