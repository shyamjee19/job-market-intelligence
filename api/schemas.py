from datetime import date, datetime

from pydantic import BaseModel


class JobSummary(BaseModel):
    job_id: int
    company: str | None
    position: str | None
    location: str | None
    salary_min: int | None
    salary_max: int | None
    date_posted: date | None
    tags: list[str]
    job_url: str | None
    apply_url: str | None


class JobDetail(JobSummary):
    description: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class JobListResponse(BaseModel):
    items: list[JobSummary]
    total: int
    page: int
    page_size: int


class SummaryStats(BaseModel):
    total_jobs: int
    total_companies: int
    total_locations: int
    avg_salary_min: float | None
    avg_salary_max: float | None


class CountByLabel(BaseModel):
    label: str
    count: int


class PostingsByDate(BaseModel):
    date: date
    count: int


class SalaryBucket(BaseModel):
    bucket_start: int
    bucket_end: int
    count: int
