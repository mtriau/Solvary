from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_drill_service
from app.models.user import User
from app.schemas.drills import DrillDetail, DrillList
from app.services.drill_service import DrillService

router = APIRouter(prefix="/v1/drills", tags=["drills"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[DrillService, Depends(get_drill_service)]


@router.get("", response_model=DrillList)
async def list_drills(user: CurrentUser, service: Service) -> DrillList:
    """Every drill grouped by topic, with this user's progress."""
    return await service.list(user)


@router.get("/{slug}", response_model=DrillDetail)
async def get_drill(slug: str, user: CurrentUser, service: Service) -> DrillDetail:
    """One drill: statement, starter, provided tests, editorial, navigation."""
    return await service.get(user, slug)
