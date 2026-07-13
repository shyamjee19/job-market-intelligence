from etl.validate import validate_raw_record


def test_valid_remoteok_record_has_no_errors():
    raw = {"id": "123", "company": "Acme", "position": "Engineer"}
    assert validate_raw_record("remoteok", raw) == []


def test_remoteok_missing_company_is_rejected():
    raw = {"id": "123", "company": "", "position": "Engineer"}
    errors = validate_raw_record("remoteok", raw)
    assert "missing required field 'company'" in errors


def test_valid_arbeitnow_record_has_no_errors():
    raw = {"slug": "abc-123", "company_name": "Acme", "title": "Engineer"}
    assert validate_raw_record("arbeitnow", raw) == []


def test_arbeitnow_missing_slug_is_rejected():
    raw = {"slug": None, "company_name": "Acme", "title": "Engineer"}
    errors = validate_raw_record("arbeitnow", raw)
    assert "missing required field 'slug'" in errors


def test_non_dict_record_is_rejected():
    errors = validate_raw_record("remoteok", "not a dict")
    assert len(errors) == 1


def test_unknown_source_has_no_required_fields():
    assert validate_raw_record("unknown-source", {}) == []
