"""GitHub OAuth2 (authorization code flow) - https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps

Inactive until GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET are set - same
"unconfigured -> inactive" pattern as every other optional integration.
"""
from urllib.parse import urlencode

import requests

from auth.oauth.base import OAuthUserInfo
from config.settings import settings
from utils.exceptions import APIRequestError

_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_TOKEN_URL = "https://github.com/login/oauth/access_token"
_USER_URL = "https://api.github.com/user"
_EMAILS_URL = "https://api.github.com/user/emails"

is_configured = bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)


def get_authorize_url(state: str) -> str:
    if not is_configured:
        raise APIRequestError("GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET are not set")

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


def _fetch_primary_email(access_token: str) -> str | None:
    """GitHub only includes `email` on /user if the user made it public -
    otherwise it's null and the verified primary address has to come from
    the separate /user/emails endpoint instead."""
    response = requests.get(
        _EMAILS_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        timeout=settings.API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    for entry in response.json():
        if entry.get("primary") and entry.get("verified"):
            return entry["email"]
    return None


def fetch_user_info(code: str) -> OAuthUserInfo:
    if not is_configured:
        raise APIRequestError("GITHUB_CLIENT_ID/GITHUB_CLIENT_SECRET are not set")

    token_response = requests.post(
        _TOKEN_URL,
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        },
        headers={"Accept": "application/json"},
        timeout=settings.API_TIMEOUT_SECONDS,
    )
    token_response.raise_for_status()
    token_payload = token_response.json()
    if "access_token" not in token_payload:
        raise APIRequestError(f"GitHub token exchange failed: {token_payload}")
    access_token = token_payload["access_token"]

    user_response = requests.get(
        _USER_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        timeout=settings.API_TIMEOUT_SECONDS,
    )
    user_response.raise_for_status()
    user_payload = user_response.json()

    email = user_payload.get("email") or _fetch_primary_email(access_token)
    if not email:
        raise APIRequestError("GitHub account has no accessible email address")

    return OAuthUserInfo(
        provider_id=str(user_payload["id"]),
        email=email,
        full_name=user_payload.get("name") or user_payload.get("login"),
    )
