import csv
import io

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from api.schemas import (
    CountByLabel,
    HiringTrend,
    JobDetail,
    JobListResponse,
    PostingsByDate,
    SalaryBucket,
    SummaryStats,
)
from database import queries
from utils.exceptions import DatabaseError
from utils.logger import logger

app = FastAPI(title="job-market-intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseError)
def handle_database_error(request: Request, exc: DatabaseError):
    logger.error("Database error handling %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/jobs", response_model=JobListResponse)
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


@app.get("/api/jobs/export.csv")
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


@app.get("/api/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: int):
    job = queries.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/companies", response_model=list[CountByLabel])
def get_companies(limit: int = Query(50, ge=1, le=200)):
    return [{"label": r["company"], "count": r["count"]} for r in queries.list_companies(limit)]


@app.get("/api/skills", response_model=list[CountByLabel])
def get_skills(limit: int = Query(50, ge=1, le=200)):
    return [{"label": r["tag"], "count": r["count"]} for r in queries.list_skills(limit)]


@app.get("/api/stats/summary", response_model=SummaryStats)
def get_summary():
    return queries.summary_stats()


@app.get("/api/stats/top-companies", response_model=list[CountByLabel])
def get_top_companies(limit: int = Query(10, ge=1, le=50), source: str | None = None):
    return [{"label": r["company"], "count": r["count"]} for r in queries.top_companies(limit, source)]


@app.get("/api/stats/top-tags", response_model=list[CountByLabel])
def get_top_tags(limit: int = Query(15, ge=1, le=50), source: str | None = None, category: str | None = None):
    return [{"label": r["tag"], "count": r["count"]} for r in queries.top_tags(limit, source, category)]


@app.get("/api/stats/postings-by-date", response_model=list[PostingsByDate])
def get_postings_by_date():
    return [{"date": r["date_posted"], "count": r["count"]} for r in queries.postings_by_date()]


@app.get("/api/stats/salary-distribution", response_model=list[SalaryBucket])
def get_salary_distribution():
    return [
        {"bucket_start": r["bucket_start"], "bucket_end": r["bucket_start"] + 20000, "count": r["count"]}
        for r in queries.salary_distribution()
    ]


@app.get("/api/stats/sources", response_model=list[CountByLabel])
def get_sources():
    return [{"label": r["source"], "count": r["count"]} for r in queries.sources_breakdown()]


@app.get("/api/stats/hiring-map", response_model=list[CountByLabel])
def get_hiring_map():
    """Best-effort: country is inferred from free-text location, so
    postings whose location didn't match a known country/city aren't
    included (see utils/geo.py)."""
    return [{"label": r["country"], "count": r["count"]} for r in queries.hiring_map()]


@app.get("/api/stats/trend", response_model=HiringTrend)
def get_trend():
    return queries.hiring_trend()
