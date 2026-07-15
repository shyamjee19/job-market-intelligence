"""Schema validation for raw records, before they're normalized.

Each source has a small set of fields a posting can't be useful without.
A record that fails validation is never silently dropped - the pipeline
records why (see database `rejected_records` table via etl/load.py) so
data-quality issues stay visible instead of vanishing.
"""
from config.constants import SOURCE_ADZUNA, SOURCE_ARBEITNOW, SOURCE_REMOTEOK, SOURCE_USAJOBS

# source -> required raw field paths (must be present and non-empty).
# Dotted paths ("a.b") look up nested dict fields - USAJobs buries
# everything under MatchedObjectDescriptor.
REQUIRED_FIELDS: dict[str, list[str]] = {
    SOURCE_REMOTEOK: ["id", "company", "position"],
    SOURCE_ARBEITNOW: ["slug", "company_name", "title"],
    SOURCE_ADZUNA: ["id", "title", "company.display_name"],
    SOURCE_USAJOBS: [
        "MatchedObjectId",
        "MatchedObjectDescriptor.PositionTitle",
        "MatchedObjectDescriptor.OrganizationName",
    ],
}


def _get_nested(raw: dict, path: str):
    value = raw
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def validate_raw_record(source: str, raw: dict) -> list[str]:
    """Returns a list of validation error reasons; empty means valid."""
    errors: list[str] = []

    if not isinstance(raw, dict):
        return [f"record is not an object (got {type(raw).__name__})"]

    required = REQUIRED_FIELDS.get(source, [])
    for field in required:
        value = _get_nested(raw, field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required field '{field}'")

    return errors
