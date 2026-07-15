"""Generic in-memory sliding-window rate limiter, keyed by (namespace,
client_id) so independent endpoint groups (AI chat, auth, general API)
each get their own counter instead of sharing one bucket.

No Redis needed at this scale - if this ever runs behind multiple worker
processes, the window is per-process, not shared; that's the point at
which this would need to move to Redis (INCR + EXPIRE) instead.
"""
import time
from collections import defaultdict

_WINDOW_SECONDS = 60

_requests: dict[tuple[str, str], list[float]] = defaultdict(list)


def check_rate_limit(namespace: str, client_id: str, limit: int) -> bool:
    """Returns True if the request is allowed, False if rate-limited."""
    now = time.time()
    window_start = now - _WINDOW_SECONDS
    key = (namespace, client_id)

    timestamps = _requests[key]
    timestamps[:] = [t for t in timestamps if t > window_start]

    if len(timestamps) >= limit:
        return False

    timestamps.append(now)
    return True


def reset(namespace: str, client_id: str) -> None:
    """Test helper - clears one bucket's state."""
    _requests.pop((namespace, client_id), None)
