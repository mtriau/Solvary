from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_user_service
from app.models.user import User
from app.schemas.users import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await user_service.get_me(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return await user_service.get_by_id(user_id)
