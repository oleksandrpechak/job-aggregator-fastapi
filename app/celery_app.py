from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "job_aggregator",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "ingest-dou-python-junior": {
        "task": "app.tasks.ingest_dou_jobs",
        "schedule": crontab(minute=0, hour="*/2"),
    },
}
celery_app.conf.timezone = "Europe/Kyiv"
celery_app.autodiscover_tasks(["app"])