"""FastAPI dependencies for authentication/authorization.

`get_current_user` extracts and validates a JWT from the Authorization
header and loads the corresponding user; `require_admin` builds on it to
additionally enforce the admin role; `get_optional_user` never raises,
for endpoints that behave differently when logged in but don't require it.
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.security import ACCESS_TOKEN_TYPE, decode_token
from database.users_queries import get_user_by_id

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from None
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = get_user_by_id(int(payload["sub"]))
    if user is None or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme)) -> dict | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
