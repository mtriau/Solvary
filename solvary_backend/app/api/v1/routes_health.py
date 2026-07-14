from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    # In production, check DB connectivity, cache, etc.
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(UTC),
    )
