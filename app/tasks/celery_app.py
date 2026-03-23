import os

from celery import Celery

_redis = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "sales_system",
    broker=_redis,
    backend=_redis,
)
celery_app.autodiscover_tasks(["app.tasks"])
