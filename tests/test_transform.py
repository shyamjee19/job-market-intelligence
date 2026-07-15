from etl.transform import transform_jobs


def make_remoteok_raw(**overrides):
    base = {
        "id": "123",
        "company": "Acme",
        "position": "Backend Engineer",
        "location": "Remote",
        "salary_min": 70000,
        "salary_max": 90000,
        "date": "2026-07-09T10:30:04+00:00",
        "tags": ["python", "django"],
        "url": "https://remoteok.com/remote-jobs/123",
        "apply_url": "https://remoteok.com/apply/123",
        "description": "Build things.",
    }
    base.update(overrides)
    return base


def make_arbeitnow_raw(**overrides):
    base = {
        "slug": "backend-engineer-berlin-123",
        "company_name": "Acme",
        "title": "Backend Engineer",
        "location": "Berlin",
        "remote": True,
        "url": "https://arbeitnow.com/jobs/companies/acme/backend-engineer-berlin-123",
        "tags": ["python"],
        "job_types": ["full time"],
        "created_at": 1783593004,
        "description": "Build things.",
    }
    base.update(overrides)
    return base


def make_adzuna_raw(**overrides):
    base = {
        "id": "4567890",
        "title": "Backend Engineer",
        "company": {"display_name": "Acme"},
        "location": {"display_name": "London, UK"},
        "salary_min": 50000.0,
        "salary_max": 70000.0,
        "created": "2026-07-09T10:30:04Z",
        "category": {"label": "IT Jobs"},
        "redirect_url": "https://www.adzuna.co.uk/land/ad/4567890",
        "description": "Build things.",
    }
    base.update(overrides)
    return base


def make_usajobs_raw(**overrides):
    descriptor = {
        "PositionTitle": "IT Specialist",
        "OrganizationName": "Department of Defense",
        "PositionLocationDisplay": "Washington, DC",
        "PositionRemuneration": [{"MinimumRange": "70000", "MaximumRange": "90000"}],
        "PublicationStartDate": "2026-07-01",
        "JobCategory": [{"Name": "Information Technology"}],
        "PositionURI": "https://www.usajobs.gov/job/999888",
        "UserArea": {"Details": {"JobSummary": "Build things."}},
    }
    descriptor.update(overrides.pop("descriptor_overrides", {}))
    base = {"MatchedObjectId": "999888", "MatchedObjectDescriptor": descriptor}
    base.update(overrides)
    return base


def test_transforms_valid_adzuna_record():
    result = transform_jobs("adzuna", [make_adzuna_raw()])
    assert len(result) == 1
    job = result[0]
    assert job["source"] == "adzuna"
    assert job["external_id"] == "4567890"
    assert job["company"] == "Acme"
    assert job["location"] == "London, UK"
    assert job["country"] == "United Kingdom"
    assert job["salary_min"] == 50000
    assert job["tags"] == ["IT Jobs"]


def test_adzuna_missing_company_object_does_not_crash():
    result = transform_jobs("adzuna", [make_adzuna_raw(company=None)])
    assert result[0]["company"] is None


def test_transforms_valid_usajobs_record():
    result = transform_jobs("usajobs", [make_usajobs_raw()])
    assert len(result) == 1
    job = result[0]
    assert job["source"] == "usajobs"
    assert job["external_id"] == "999888"
    assert job["company"] == "Department of Defense"
    assert job["country"] == "United States"
    assert job["salary_min"] == 70000
    assert job["salary_max"] == 90000
    assert job["tags"] == ["Information Technology"]
    assert job["date_posted"] is not None


def test_usajobs_detects_remote_from_location_display():
    result = transform_jobs(
        "usajobs",
        [make_usajobs_raw(descriptor_overrides={"PositionLocationDisplay": "Anywhere in the U.S. (remote)"})],
    )
    assert result[0]["remote_type"] == "remote"


def test_transforms_valid_remoteok_record():
    result = transform_jobs("remoteok", [make_remoteok_raw()])
    assert len(result) == 1
    job = result[0]
    assert job["source"] == "remoteok"
    assert job["external_id"] == "123"
    assert job["company"] == "Acme"
    assert job["remote_type"] == "remote"
    assert job["salary_min"] == 70000
    assert job["tags"] == ["python", "django"]


def test_transforms_valid_arbeitnow_record():
    result = transform_jobs("arbeitnow", [make_arbeitnow_raw()])
    assert len(result) == 1
    job = result[0]
    assert job["source"] == "arbeitnow"
    assert job["external_id"] == "backend-engineer-berlin-123"
    assert job["remote_type"] == "remote"
    assert job["salary_min"] is None
    assert "python" in job["tags"] and "full time" in job["tags"]
    assert job["date_posted"] is not None


def test_arbeitnow_onsite_when_not_remote():
    result = transform_jobs("arbeitnow", [make_arbeitnow_raw(remote=False)])
    assert result[0]["remote_type"] == "onsite"


def test_dedupes_by_external_id_keeping_last():
    result = transform_jobs(
        "remoteok",
        [make_remoteok_raw(position="First"), make_remoteok_raw(position="Second")],
    )
    assert len(result) == 1
    assert result[0]["position"] == "Second"


def test_treats_zero_salary_as_unknown():
    result = transform_jobs("remoteok", [make_remoteok_raw(salary_min=0, salary_max=0)])
    assert result[0]["salary_min"] is None
    assert result[0]["salary_max"] is None
