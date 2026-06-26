from celery import Celery
# from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "job_aggregator",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.autodiscover_tasks(["app"])

celery_app.conf.beat_schedule = {
    "ingest-dou-python-every-30-sec": {
        "task": "app.tasks.ingest_dou",
        "schedule": 60 * 60 * 2,
        "args": ["6a3e2cfffdf8a3c29947cdb5"],
    },
     "ingest-dou-ruby-every-2-hours": {
        "task": "app.tasks.ingest_dou",
        "schedule": 60 * 60 * 2,
        "args": ["6a3e6cacfdf8a3c29947f68d"],
    },
}

celery_app.conf.timezone = settings.celery_app_timezone

