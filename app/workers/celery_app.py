from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings
settings = get_settings()
celery_app = Celery("ai_job_assistant", broker=settings.celery_broker_url, backend=settings.celery_result_backend, include=["app.workers.tasks"])
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"], timezone="UTC", enable_utc=True, task_track_started=True, broker_connection_retry_on_startup=True)
celery_app.conf.beat_schedule = {"discover-public-jobs": {"task": "phase3.discover_default_jobs", "schedule": crontab(minute=5, hour="*/6")}, "run-active-job-alerts": {"task": "phase3.run_all_alerts", "schedule": crontab(minute=20, hour="*/6")}, "sync-recruiter-email": {"task": "phase3.sync_recruiter_email", "schedule": crontab(minute="*/30")}}
