"""Celery application configuration."""

import os
from celery import Celery
from celery.schedules import crontab

# Initialize Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("pm_assistant", broker=redis_url, backend=redis_url)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Beat schedule - all scheduled tasks
celery_app.conf.beat_schedule = {
    # Daily full sync at 6 AM UTC
    "daily-sync": {
        "task": "app.jobs.sync.daily_sync_for_all_tenants",
        "schedule": crontab(hour=6, minute=0),
    },
    # Morning standups at 9 AM UTC (start of workday)
    "morning-standups": {
        "task": "app.jobs.scheduled_workflows.send_morning_standups_for_all_tenants",
        "schedule": crontab(hour=9, minute=0),
    },
}
