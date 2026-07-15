from fastapi import APIRouter, Query

from api.schemas import CountByLabel, HiringTrend, PostingsByDate, SalaryBucket, SummaryStats
from database import queries
from utils.cache import cached

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=SummaryStats)
@cached()
def get_summary():
    return queries.summary_stats()


@router.get("/top-companies", response_model=list[CountByLabel])
@cached()
def get_top_companies(limit: int = Query(10, ge=1, le=50), source: str | None = None):
    return [{"label": r["company"], "count": r["count"]} for r in queries.top_companies(limit, source)]


@router.get("/top-tags", response_model=list[CountByLabel])
@cached()
def get_top_tags(limit: int = Query(15, ge=1, le=50), source: str | None = None, category: str | None = None):
    return [{"label": r["tag"], "count": r["count"]} for r in queries.top_tags(limit, source, category)]


@router.get("/postings-by-date", response_model=list[PostingsByDate])
@cached()
def get_postings_by_date():
    return [{"date": r["date_posted"], "count": r["count"]} for r in queries.postings_by_date()]


@router.get("/salary-distribution", response_model=list[SalaryBucket])
@cached()
def get_salary_distribution():
    return [
        {"bucket_start": r["bucket_start"], "bucket_end": r["bucket_start"] + 20000, "count": r["count"]}
        for r in queries.salary_distribution()
    ]


@router.get("/sources", response_model=list[CountByLabel])
@cached()
def get_sources():
    return [{"label": r["source"], "count": r["count"]} for r in queries.sources_breakdown()]


@router.get("/hiring-map", response_model=list[CountByLabel])
@cached()
def get_hiring_map():
    """Best-effort: country is inferred from free-text location, so
    postings whose location didn't match a known country/city aren't
    included (see utils/geo.py)."""
    return [{"label": r["country"], "count": r["count"]} for r in queries.hiring_map()]


@router.get("/trend", response_model=HiringTrend)
@cached(ttl_seconds=300)
def get_trend():
    return queries.hiring_trend()
