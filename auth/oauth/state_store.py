"""Short-lived in-memory stores for the OAuth2 flow:

- CSRF `state` tokens, created when redirecting to the provider and
  consumed (once) on callback, so a callback can't be forged by an
  attacker who never went through the authorize step.
- One-time exchange codes, created after a successful callback and
  consumed (once) by the frontend's POST /auth/oauth/exchange - this
  keeps real JWTs out of the browser's URL bar, history, and referrer
  headers, which a direct "redirect with tokens in the query string"
  approach would not.

Dev-grade like ai/services/conversation_store.py - a multi-worker
deployment would need this shared (Redis), not per-process memory.
"""
import time
import uuid

_STATE_TTL_SECONDS = 600
_EXCHANGE_TTL_SECONDS = 60

_pending_states: dict[str, float] = {}
_exchange_codes: dict[str, tuple[dict, float]] = {}


def create_state() -> str:
    state = str(uuid.uuid4())
    _pending_states[state] = time.time() + _STATE_TTL_SECONDS
    return state


def consume_state(state: str) -> bool:
    expiry = _pending_states.pop(state, None)
    return expiry is not None and expiry > time.time()


def create_exchange_code(tokens: dict) -> str:
    code = str(uuid.uuid4())
    _exchange_codes[code] = (tokens, time.time() + _EXCHANGE_TTL_SECONDS)
    return code


def consume_exchange_code(code: str) -> dict | None:
    entry = _exchange_codes.pop(code, None)
    if entry is None:
        return None
    tokens, expiry = entry
    if expiry < time.time():
        return None
    return tokens
