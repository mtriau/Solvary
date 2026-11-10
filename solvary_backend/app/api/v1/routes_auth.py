from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import get_auth_service
from app.config import Settings, get_settings
from app.core.rate_limit import (
    client_ip,
    login_ip_limiter,
    login_limiter,
    signup_limiter,
)
from app.schemas.auth import GoogleLoginRequest, LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "solvary_refresh"


def _set_refresh_cookie(response: Response, settings: Settings, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        httponly=True,  # invisible to JS — XSS cannot exfiltrate it
        samesite="lax",
        secure=settings.environment == "production",
        path=f"{settings.api_prefix}/auth",
        max_age=settings.refresh_token_expire_days * 86400,
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=f"{settings.api_prefix}/auth")


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    await signup_limiter.check(client_ip(request))
    tokens, raw_refresh = await auth_service.register(data.name, data.email, data.password)
    _set_refresh_cookie(response, settings, raw_refresh)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    ip = client_ip(request)
    await login_ip_limiter.check(ip)
    await login_limiter.check(f"{ip}:{data.email.lower()}")
    tokens, raw_refresh = await auth_service.login(data.email, data.password)
    _set_refresh_cookie(response, settings, raw_refresh)
    return tokens


@router.post("/google", response_model=TokenResponse)
async def google_login(
    data: GoogleLoginRequest,
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    await signup_limiter.check(client_ip(request))
    tokens, raw_refresh = await auth_service.google_login(data.credential)
    _set_refresh_cookie(response, settings, raw_refresh)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Rotate the refresh token (httpOnly cookie) → new access + cookie."""
    raw = request.cookies.get(REFRESH_COOKIE, "")
    try:
        tokens, new_refresh = await auth_service.refresh(raw)
    except Exception:
        _clear_refresh_cookie(response, settings)
        raise
    _set_refresh_cookie(response, settings, new_refresh)
    return tokens


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    await auth_service.logout(request.cookies.get(REFRESH_COOKIE))
    _clear_refresh_cookie(response, settings)
