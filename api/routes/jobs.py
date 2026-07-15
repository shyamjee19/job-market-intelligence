import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.schemas import CountByLabel, JobDetail, JobListResponse
from database import queries

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=JobListResponse)
def get_jobs(
    search: str | None = None,
    company: str | None = None,
    location: str | None = None,
    tag: str | None = None,
    source: str | None = None,
    salary_min: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=queries.MAX_PAGE_SIZE),
):
    rows, total = queries.list_jobs(
        search=search,
        company=company,
        location=location,
        tag=tag,
        source=source,
        salary_min=salary_min,
        page=page,
        page_size=page_size,
    )
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/jobs/export.csv")
def export_jobs_csv(
    search: str | None = None,
    company: str | None = None,
    location: str | None = None,
    tag: str | None = None,
    source: str | None = None,
    salary_min: int | None = None,
):
    """Exports every job matching the given filters (not just one page) as CSV."""
    rows, _ = queries.list_jobs(
        search=search, company=company, location=location, tag=tag,
        source=source, salary_min=salary_min, page=1, page_size=queries.MAX_PAGE_SIZE,
    )

    buffer = io.StringIO()
    fieldnames = [
        "id", "source", "position", "company", "location", "remote_type",
        "salary_min", "salary_max", "date_posted", "tags", "job_url", "apply_url",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "tags": ", ".join(row.get("tags") or [])})

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobs.csv"},
    )


@router.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: int):
    job = queries.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/companies", response_model=list[CountByLabel])
def get_companies(limit: int = Query(50, ge=1, le=200)):
    return [{"label": r["company"], "count": r["count"]} for r in queries.list_companies(limit)]


@router.get("/skills", response_model=list[CountByLabel])
def get_skills(limit: int = Query(50, ge=1, le=200)):
    return [{"label": r["tag"], "count": r["count"]} for r in queries.list_skills(limit)]
