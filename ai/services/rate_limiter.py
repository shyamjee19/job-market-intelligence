"""Thin wrapper over utils.rate_limiter for the AI chat endpoint - kept
in ai/ so ai/router.py's dependency graph stays self-contained within the
module, matching the rest of ai/'s structure."""
from config.settings import settings
from utils.rate_limiter import check_rate_limit as _check_rate_limit

_NAMESPACE = "ai-chat"


def check_rate_limit(client_id: str) -> bool:
    return _check_rate_limit(_NAMESPACE, client_id, settings.AI_RATE_LIMIT_PER_MINUTE)
