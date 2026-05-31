from celery import Celery

from app.core.config import get_settings, is_missing_or_placeholder


settings = get_settings()

broker_url = settings.celery_broker_url
result_backend = settings.celery_result_backend

if is_missing_or_placeholder(broker_url):
    broker_url = "memory://"
if is_missing_or_placeholder(result_backend):
    result_backend = "cache+memory://"

celery_app = Celery(
    settings.app_name,
    broker=broker_url,
    backend=result_backend,
    include=["app.workers.tasks.debug"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
)

# Celery CLI discovers this name when using:
# celery -A app.workers.celery_app worker --loglevel=INFO
app = celery_app
