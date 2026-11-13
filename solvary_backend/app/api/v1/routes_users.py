from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_user_service
from app.core.rate_limit import ai_key_test_limiter
from app.models.user import User
from app.schemas.interviewer import AiKeySet, AiKeyStatus, AiKeyTestResult
from app.schemas.users import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[UserService, Depends(get_user_service)]


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser, user_service: Service) -> UserResponse:
    return await user_service.get_me(current_user)


# ── Anthropic API key for the interviewer agent ───────────────────
# Declared before /{user_id} so "me" never matches as an id.


@router.get("/me/ai-key", response_model=AiKeyStatus)
async def get_ai_key(current_user: CurrentUser, user_service: Service) -> AiKeyStatus:
    """Whether a key is configured and where it comes from; never the key itself."""
    return await user_service.get_ai_key_status(current_user)


@router.put("/me/ai-key", response_model=AiKeyStatus)
async def set_ai_key(
    data: AiKeySet, current_user: CurrentUser, user_service: Service
) -> AiKeyStatus:
    return await user_service.set_ai_key(current_user, data.api_key)


@router.delete("/me/ai-key", response_model=AiKeyStatus)
async def clear_ai_key(current_user: CurrentUser, user_service: Service) -> AiKeyStatus:
    return await user_service.clear_ai_key(current_user)


@router.post("/me/ai-key/test", response_model=AiKeyTestResult)
async def test_ai_key(current_user: CurrentUser, user_service: Service) -> AiKeyTestResult:
    """One tiny Claude request on the configured key (5/min)."""
    await ai_key_test_limiter.check(current_user.id)
    return await user_service.test_ai_key(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _current_user: CurrentUser,
    user_service: Service,
) -> UserResponse:
    return await user_service.get_by_id(user_id)
