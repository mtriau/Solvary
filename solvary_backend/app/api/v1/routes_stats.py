from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_stats_service
from app.models.user import User
from app.schemas.stats import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter(prefix="/v1/stats", tags=["stats"])


@router.get("/me", response_model=StatsResponse)
async def my_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[StatsService, Depends(get_stats_service)],
) -> StatsResponse:
    return await service.compute(current_user)
