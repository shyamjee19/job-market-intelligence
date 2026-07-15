"""FastAPI app entrypoint. Routers are versioned under /api/v1 - see
api/routes/ (jobs, stats, users, admin), auth/router.py, and ai/router.py
for the actual endpoint implementations. This module only wires them
together plus cross-cutting concerns (CORS, exception handling, health).
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai.router import router as ai_router
from api.routes.admin import router as admin_router
from api.routes.jobs import router as jobs_router
from api.routes.stats import router as stats_router
from api.routes.users import router as users_router
from auth.router import router as auth_router
from config.settings import settings
from database.connection import get_connection
from utils.cache import get_cache
from utils.exceptions import DatabaseError
from utils.logger import logger

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="job-market-intelligence API",
    version="1.0.0",
    description="Multi-source job market data, an AI assistant, and user accounts (saved jobs, alerts, profiles).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(jobs_router, prefix=API_V1_PREFIX)
app.include_router(stats_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["auth"])
app.include_router(users_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(ai_router, prefix=f"{API_V1_PREFIX}/ai", tags=["ai"])


@app.exception_handler(DatabaseError)
def handle_database_error(request: Request, exc: DatabaseError):
    logger.error("Database error handling %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.get("/health", tags=["health"])
def health():
    """Liveness/readiness probe. Checks the database is actually
    reachable, not just that the process is up - a common gap that lets
    a load balancer keep routing traffic to an instance that can't serve
    any real request. Redis is only checked when configured - its absence
    is a supported degrade-to-in-memory state, not a failure."""
    checks: dict[str, bool] = {"database": _check_database()}
    if settings.REDIS_URL:
        checks["redis"] = _check_redis()

    status_ok = all(checks.values())
    return JSONResponse(
        status_code=200 if status_ok else 503,
        content={
            "status": "ok" if status_ok else "degraded",
            "version": app.version,
            "cache_backend": get_cache().name,
            "checks": checks,
        },
    )


def _check_database() -> bool:
    try:
        conn = get_connection()
        conn.close()
        return True
    except DatabaseError:
        return False


def _check_redis() -> bool:
    """A fresh ping, not just "did the cached Cache singleton resolve to
    Redis at startup" - that would miss Redis going down mid-run, since
    get_cache() only resolves its backend once and then reuses it."""
    try:
        import redis

        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        client.ping()
        return True
    except Exception:
        return False
