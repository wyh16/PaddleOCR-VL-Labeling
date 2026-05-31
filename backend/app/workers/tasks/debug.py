from datetime import UTC, datetime

from app.workers.celery_app import celery_app


@celery_app.task(name="debug_ping")
def debug_ping() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }
