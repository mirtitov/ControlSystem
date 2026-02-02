from celery import Celery
from celery.schedules import crontab

from src.config import settings

# Create Celery app
celery_app = Celery(
    "production_control",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Auto-close expired batches - every day at 01:00
    "auto-close-expired-batches": {
        "task": "src.tasks.auto_close_expired_batches",
        "schedule": crontab(hour=1, minute=0),
    },
    # Cleanup old files - every day at 02:00
    "cleanup-old-files": {
        "task": "src.tasks.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),
    },
    # Update statistics - every 5 minutes
    "update-statistics": {
        "task": "src.tasks.update_cached_statistics",
        "schedule": crontab(minute="*/5"),
    },
    # Retry failed webhooks - every 15 minutes
    "retry-failed-webhooks": {
        "task": "src.tasks.retry_failed_webhooks",
        "schedule": crontab(minute="*/15"),
    },
}
