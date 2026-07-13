"""Small, pure data-cleaning helpers used by the ETL transform step.

Kept dependency-free and side-effect-free on purpose so they're trivial
to unit test without a database or network access.
"""
import html
from datetime import date, datetime
from typing import Iterable, Optional


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


def dedupe_by_key(records: Iterable[dict], key: str) -> list[dict]:
    """Keep the last occurrence of each key - later records in the same
    batch are assumed to be the freshest."""
    deduped: dict = {}
    for record in records:
        deduped[record.get(key)] = record
    return list(deduped.values())
