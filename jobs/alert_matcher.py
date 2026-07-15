"""Job-alert matching: for each active alert, finds new postings matching
its saved criteria and sends (or logs, if SMTP isn't configured - see
utils/email.py) a notification.

Pure business logic with no Celery dependency, so it's callable directly
right now - `python main.py check-alerts` - without needing Redis or a
running worker. jobs/tasks.py wraps this same function for scheduled
execution once Redis is available.
"""
from database.users_queries import get_user_by_id, list_active_alerts, match_jobs_for_alert
from database.users_repository import log_notification, mark_alert_checked
from utils.email import send_email
from utils.logger import logger


def _format_alert_email(alert: dict, jobs: list[dict]) -> tuple[str, str]:
    subject = f'JobPulse alert "{alert["name"]}": {len(jobs)} new job(s)'
    lines = [f"- {j['position']} at {j['company']} ({j.get('location') or 'location not specified'})" for j in jobs]
    body = "New postings matching your alert:\n\n" + "\n".join(lines)
    return subject, body


def check_all_alerts() -> dict:
    alerts = list_active_alerts()
    results = {"alerts_checked": 0, "notifications_sent": 0}

    for alert in alerts:
        matches = match_jobs_for_alert(alert)
        results["alerts_checked"] += 1

        if matches:
            user = get_user_by_id(alert["user_id"])
            subject, body = _format_alert_email(alert, matches)
            sent = send_email(user["email"], subject, body)
            log_notification(
                alert["user_id"], subject, body, alert_id=alert["alert_id"], status="sent" if sent else "logged"
            )
            # match_jobs_for_alert orders newest-first, so matches[0] is
            # the new high-water mark - nothing at or before it gets
            # re-notified on the next check.
            mark_alert_checked(alert["alert_id"], last_notified_job_key=matches[0]["id"])
            results["notifications_sent"] += 1
        else:
            mark_alert_checked(alert["alert_id"])

    logger.info("Alert check complete: %s", results)
    return results
