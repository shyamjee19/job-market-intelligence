from jobs.alert_matcher import check_all_alerts
from jobs.celery_app import celery_app


@celery_app.task(name="jobs.tasks.check_job_alerts_task")
def check_job_alerts_task():
    return check_all_alerts()
