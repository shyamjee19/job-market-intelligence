"""Password hashing and JWT creation/verification - pure functions, no
database access. auth/dependencies.py and auth/router.py build on these.
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config.settings import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # malformed hash (e.g. an OAuth-only account with no password set)
        return False


def _create_token(user_id: int, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        user_id, role, ACCESS_TOKEN_TYPE, timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: int, role: str) -> str:
    return _create_token(
        user_id, role, REFRESH_TOKEN_TYPE, timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str) -> dict:
    """Raises a jwt.PyJWTError subclass (ExpiredSignatureError,
    InvalidTokenError, ...) on any invalid/expired token - callers decide
    how to turn that into an HTTP response."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_refresh_token(token: str) -> str:
    """Refresh tokens are stored hashed (like passwords) so a database
    leak doesn't hand out live sessions. Plain SHA-256 is fine here (not
    bcrypt): the token itself is already a high-entropy random JWT, not a
    human-chosen password vulnerable to a dictionary attack."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
