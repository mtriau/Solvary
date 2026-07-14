from datetime import UTC, datetime
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text

from app.config import Settings, get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness: the process is up and serving."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(UTC),
    )


@router.get("/ready")
async def readiness_check(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Readiness: dependencies are actually reachable. Returns 503 with
    per-check detail when any dependency is down — orchestrators use this
    to gate traffic."""
    checks: dict[str, str] = {}

    if settings.use_mock_db:
        checks["database"] = "ok (mock)"
    else:
        try:
            from app.db.engine import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {type(e).__name__}"

    if settings.execution_provider == "piston":
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{settings.piston_base_url}/api/v2/runtimes", timeout=3.0
                )
                r.raise_for_status()
                checks["piston"] = "ok" if r.json() else "error: no runtimes installed"
        except Exception as e:
            checks["piston"] = f"error: {type(e).__name__}"
    else:
        checks["execution"] = f"ok ({settings.execution_provider})"

    healthy = all(v.startswith("ok") for v in checks.values())
    if not healthy:
        response.status_code = 503
    return {"status": "ready" if healthy else "not ready", "checks": checks}
