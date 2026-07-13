from etl.transform import transform_jobs


def make_raw(**overrides):
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


def test_transforms_valid_record():
    result = transform_jobs([make_raw()])
    assert len(result) == 1
    job = result[0]
    assert job["job_id"] == 123
    assert job["company"] == "Acme"
    assert job["salary_min"] == 70000
    assert job["tags"] == ["python", "django"]


def test_drops_record_missing_required_field():
    result = transform_jobs([make_raw(company=None)])
    assert result == []


def test_drops_record_missing_job_id():
    result = transform_jobs([make_raw(id=None)])
    assert result == []


def test_dedupes_by_job_id_keeping_last():
    result = transform_jobs([make_raw(position="First"), make_raw(position="Second")])
    assert len(result) == 1
    assert result[0]["position"] == "Second"


def test_treats_zero_salary_as_unknown():
    result = transform_jobs([make_raw(salary_min=0, salary_max=0)])
    assert result[0]["salary_min"] is None
    assert result[0]["salary_max"] is None
