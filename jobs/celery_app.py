"""Celery app for scheduled background work (currently: hourly job-alert
checks). Inactive in the sense that nothing runs it unless you actually
start a worker + beat process against a real Redis - see README for the
commands. The alert-matching logic itself (jobs/alert_matcher.py) works
right now with no Celery/Redis at all via `python main.py check-alerts`;
this is only the "run it automatically, on a schedule" layer on top.
"""
from celery import Celery
from celery.schedules import crontab

from config.settings import settings

celery_app = Celery(
    "job_market_intelligence",
    broker=settings.REDIS_URL or "memory://",
    backend=settings.REDIS_URL,
    include=["jobs.tasks"],
)

celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "check-job-alerts-hourly": {
        "task": "jobs.tasks.check_job_alerts_task",
        "schedule": crontab(minute=0),
    },
}
