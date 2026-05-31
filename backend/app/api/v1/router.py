from fastapi import APIRouter

from app.core.health import service_health

api_router = APIRouter()


@api_router.get("/health", tags=["system"], summary="Health Check")
async def health_check() -> dict[str, object]:
    return service_health()
