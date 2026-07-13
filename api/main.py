from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import (
    CountByLabel,
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
    salary_min: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=queries.MAX_PAGE_SIZE),
):
    rows, total = queries.list_jobs(
        search=search,
        company=company,
        location=location,
        tag=tag,
        salary_min=salary_min,
        page=page,
        page_size=page_size,
    )
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@app.get("/api/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: int):
    job = queries.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/stats/summary", response_model=SummaryStats)
def get_summary():
    return queries.summary_stats()


@app.get("/api/stats/top-companies", response_model=list[CountByLabel])
def get_top_companies(limit: int = Query(10, ge=1, le=50)):
    return [{"label": r["company"], "count": r["count"]} for r in queries.top_companies(limit)]


@app.get("/api/stats/top-tags", response_model=list[CountByLabel])
def get_top_tags(limit: int = Query(15, ge=1, le=50)):
    return [{"label": r["tag"], "count": r["count"]} for r in queries.top_tags(limit)]


@app.get("/api/stats/postings-by-date", response_model=list[PostingsByDate])
def get_postings_by_date():
    return [{"date": r["date_posted"], "count": r["count"]} for r in queries.postings_by_date()]


@app.get("/api/stats/salary-distribution", response_model=list[SalaryBucket])
def get_salary_distribution():
    return [
        {"bucket_start": r["bucket_start"], "bucket_end": r["bucket_start"] + 20000, "count": r["count"]}
        for r in queries.salary_distribution()
    ]
