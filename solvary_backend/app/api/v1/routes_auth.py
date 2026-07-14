from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await auth_service.register(data.name, data.email, data.password)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await auth_service.login(data.email, data.password)
