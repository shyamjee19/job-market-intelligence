from datetime import date

from utils.helper import clean_text, dedupe_by_key, normalize_salary, normalize_tags, parse_date


def test_clean_text_strips_whitespace():
    assert clean_text("  Remote  ") == "Remote"


def test_clean_text_empty_becomes_none():
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_clean_text_decodes_html_entities():
    assert clean_text("Woodard &amp; Curran") == "Woodard & Curran"


def test_parse_date_valid_iso8601():
    assert parse_date("2026-07-09T10:30:04+00:00") == date(2026, 7, 9)


def test_parse_date_invalid_returns_none():
    assert parse_date("not-a-date") is None
    assert parse_date(None) is None


def test_normalize_salary_treats_zero_as_unknown():
    assert normalize_salary(0, 0) == (None, None)


def test_normalize_salary_keeps_real_values():
    assert normalize_salary(70000, 90000) == (70000, 90000)


def test_normalize_salary_handles_bad_input():
    assert normalize_salary("n/a", None) == (None, None)


def test_normalize_tags_strips_and_drops_blanks():
    assert normalize_tags([" python ", "", "  ", "sql"]) == ["python", "sql"]


def test_normalize_tags_handles_none():
    assert normalize_tags(None) == []


def test_dedupe_by_key_keeps_last_occurrence():
    records = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 1, "v": "c"}]
    result = dedupe_by_key(records, "id")
    assert len(result) == 2
    assert {r["id"]: r["v"] for r in result} == {1: "c", 2: "b"}
