"""Small, pure data-cleaning helpers used by the ETL transform step.

Kept dependency-free and side-effect-free on purpose so they're trivial
to unit test without a database or network access.
"""
import html
import re
from datetime import date, datetime, timezone
from typing import Iterable, Optional

_HYBRID_PATTERN = re.compile(r"\bhybrid\b", re.IGNORECASE)


def clean_text(value) -> Optional[str]:
    """Strip whitespace, decode HTML entities (RemoteOK sends fields like
    company/position HTML-escaped, e.g. "Woodard &amp; Curran"), and
    collapse empty strings to None."""
    if value is None:
        return None
    text = html.unescape(str(value)).strip()
    return text or None


def parse_date(value) -> Optional[date]:
    """Parse RemoteOK's ISO-8601 'date' field (e.g. 2026-07-09T10:30:04+00:00)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def parse_epoch_date(value) -> Optional[date]:
    """Parse a Unix epoch (seconds) field, e.g. Arbeitnow's 'created_at'."""
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).date()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def normalize_salary(salary_min, salary_max) -> tuple[Optional[int], Optional[int]]:
    """RemoteOK reports 0/0 when salary is unknown - treat that as no data
    rather than a real $0 salary."""
    try:
        salary_min = int(salary_min) if salary_min else None
    except (TypeError, ValueError):
        salary_min = None

    try:
        salary_max = int(salary_max) if salary_max else None
    except (TypeError, ValueError):
        salary_max = None

    if salary_min == 0:
        salary_min = None
    if salary_max == 0:
        salary_max = None

    return salary_min, salary_max


def normalize_tags(tags) -> list[str]:
    if not tags:
        return []
    return [str(tag).strip() for tag in tags if str(tag).strip()]


def detect_remote_type(base_remote_type: str, *texts: Optional[str]) -> str:
    """Refines a source's coarse remote/onsite signal with a best-effort
    keyword scan: neither RemoteOK nor Arbeitnow reports "hybrid" as a
    structured field, but postings sometimes say so in the title or
    description. An explicit mention there is a stronger, more specific
    signal than the source's own boolean, so it wins."""
    for text in texts:
        if text and _HYBRID_PATTERN.search(text):
            return "hybrid"
    return base_remote_type


def dedupe_by_key(records: Iterable[dict], key: str) -> list[dict]:
    """Keep the last occurrence of each key - later records in the same
    batch are assumed to be the freshest."""
    deduped: dict = {}
    for record in records:
        deduped[record.get(key)] = record
    return list(deduped.values())
