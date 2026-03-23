from fastapi import APIRouter

from app.api.v1.router import api_v1_router

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
def api_health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(api_v1_router, prefix="/v1")
