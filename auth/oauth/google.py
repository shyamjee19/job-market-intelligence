"""Google OAuth2 (authorization code flow) - https://developers.google.com/identity/protocols/oauth2/web-server

Inactive until GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are set - auth/router.py
returns a clear 503 from the /auth/google endpoints until then, same
"unconfigured -> inactive, not broken" pattern as every other optional
integration in this project.
"""
from urllib.parse import urlencode

import requests

from auth.oauth.base import OAuthUserInfo
from config.settings import settings
from utils.exceptions import APIRequestError

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

is_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def get_authorize_url(state: str) -> str:
    if not is_configured:
        raise APIRequestError("GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are not set")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


def fetch_user_info(code: str) -> OAuthUserInfo:
    if not is_configured:
        raise APIRequestError("GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are not set")

    token_response = requests.post(
        _TOKEN_URL,
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        },
        timeout=settings.API_TIMEOUT_SECONDS,
    )
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    userinfo_response = requests.get(
        _USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=settings.API_TIMEOUT_SECONDS,
    )
    userinfo_response.raise_for_status()
    payload = userinfo_response.json()

    return OAuthUserInfo(provider_id=payload["sub"], email=payload["email"], full_name=payload.get("name"))
