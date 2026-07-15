from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from auth.dependencies import get_current_user
from auth.oauth import github as github_oauth
from auth.oauth import google as google_oauth
from auth.oauth.base import OAuthUserInfo
from auth.oauth.state_store import consume_exchange_code, consume_state, create_exchange_code, create_state
from auth.schemas import LoginRequest, ProfileOut, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from auth.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from config.settings import settings
from database.users_queries import get_profile, get_user_by_email, get_user_by_id, get_user_by_oauth_id, get_valid_refresh_token
from database.users_repository import create_user, link_oauth_id, log_audit, revoke_refresh_token, store_refresh_token
from utils.exceptions import APIRequestError
from utils.logger import logger
from utils.rate_limiter import check_rate_limit

router = APIRouter()

_NAMESPACE = "auth"


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(request: Request) -> None:
    if not check_rate_limit(_NAMESPACE, _client_ip(request), settings.AUTH_RATE_LIMIT_PER_MINUTE):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests - try again shortly.")


def _issue_tokens(user: dict) -> dict:
    access_token = create_access_token(user["user_id"], user["role"])
    refresh_token = create_refresh_token(user["user_id"], user["role"])
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    store_refresh_token(user["user_id"], hash_refresh_token(refresh_token), expires_at)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request):
    _enforce_rate_limit(request)

    if get_user_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    user = create_user(email=body.email, hashed_password=hash_password(body.password), full_name=body.full_name)
    log_audit(user["user_id"], "register", ip_address=_client_ip(request))
    return _issue_tokens(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request):
    _enforce_rate_limit(request)

    user = get_user_by_email(body.email)
    if not user or not user["hashed_password"] or not verify_password(body.password, user["hashed_password"]):
        log_audit(user["user_id"] if user else None, "login_failed", metadata={"email": body.email}, ip_address=_client_ip(request))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated")

    log_audit(user["user_id"], "login", ip_address=_client_ip(request))
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None

    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    token_hash = hash_refresh_token(body.refresh_token)
    stored = get_valid_refresh_token(token_hash)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    user = get_user_by_id(int(payload["sub"]))
    if user is None or not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Rotate: the old refresh token is single-use, so a stolen-and-replayed
    # token gets invalidated the moment the legitimate client refreshes.
    revoke_refresh_token(token_hash)
    return _issue_tokens(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest):
    revoke_refresh_token(hash_refresh_token(body.refresh_token))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return user


@router.get("/me/profile", response_model=ProfileOut)
def me_profile(user: dict = Depends(get_current_user)):
    profile = get_profile(user["user_id"])
    if profile is None:
        return ProfileOut(headline=None, bio=None, location=None, skills=[], experience_years=None, resume_filename=None, resume_uploaded_at=None)
    return profile


def _find_or_create_oauth_user(provider: str, info: OAuthUserInfo) -> dict:
    user = get_user_by_oauth_id(provider, info.provider_id)
    if user:
        return user

    existing = get_user_by_email(info.email)
    if existing:
        link_oauth_id(existing["user_id"], provider, info.provider_id)
        return get_user_by_id(existing["user_id"])

    return create_user(email=info.email, full_name=info.full_name, **{f"{provider}_id": info.provider_id})


def _start_oauth_flow(get_authorize_url) -> RedirectResponse:
    state = create_state()
    try:
        url = get_authorize_url(state)
    except APIRequestError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    return RedirectResponse(url)


def _handle_oauth_callback(provider: str, code: str, state: str, fetch_user_info, request: Request) -> RedirectResponse:
    if not consume_state(state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    try:
        info = fetch_user_info(code)
    except APIRequestError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    except Exception:
        logger.exception("[oauth-%s] callback failed", provider)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{provider} sign-in failed") from None

    user = _find_or_create_oauth_user(provider, info)
    log_audit(user["user_id"], f"oauth_login_{provider}", ip_address=_client_ip(request))

    exchange_code = create_exchange_code(_issue_tokens(user))
    return RedirectResponse(f"{settings.OAUTH_FRONTEND_REDIRECT_URL}?code={exchange_code}")


@router.get("/google")
def google_login():
    return _start_oauth_flow(google_oauth.get_authorize_url)


@router.get("/google/callback")
def google_callback(code: str, state: str, request: Request):
    return _handle_oauth_callback("google", code, state, google_oauth.fetch_user_info, request)


@router.get("/github")
def github_login():
    return _start_oauth_flow(github_oauth.get_authorize_url)


@router.get("/github/callback")
def github_callback(code: str, state: str, request: Request):
    return _handle_oauth_callback("github", code, state, github_oauth.fetch_user_info, request)


@router.post("/oauth/exchange", response_model=TokenResponse)
def oauth_exchange(code: str):
    tokens = consume_exchange_code(code)
    if tokens is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired exchange code")
    return tokens
