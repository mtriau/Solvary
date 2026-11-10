from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_interview_service, require_admin
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.interviews import (
    SessionDetail,
    SessionReview,
    SessionStart,
    SessionSummary,
    SwitchStage,
    TemplateCreate,
    TemplateDetail,
    TemplateSummary,
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/v1/interviews", tags=["interviews"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[InterviewService, Depends(get_interview_service)]


# ── templates ──────────────────────────────────────────────────────


@router.get("/templates", response_model=list[TemplateSummary])
async def list_templates(user: CurrentUser, service: Service) -> list[TemplateSummary]:
    return await service.list_templates(user)


@router.post("/templates", response_model=TemplateDetail, status_code=201)
async def create_template(
    data: TemplateCreate,
    admin: Annotated[User, Depends(require_admin)],
    service: Service,
) -> TemplateDetail:
    return await service.create_template(admin, data)


@router.get("/templates/{slug}", response_model=TemplateDetail)
async def get_template(slug: str, user: CurrentUser, service: Service) -> TemplateDetail:
    return await service.get_template(user, slug)


# ── sessions ───────────────────────────────────────────────────────


@router.post("/sessions", response_model=SessionDetail, status_code=201)
async def start_session(data: SessionStart, user: CurrentUser, service: Service) -> SessionDetail:
    return await service.start(user, data)


@router.get("/sessions", response_model=PaginatedResponse[SessionSummary])
async def list_sessions(
    user: CurrentUser,
    service: Service,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[SessionSummary]:
    return await service.list_mine(user, cursor=cursor, limit=limit)


@router.get("/sessions/active", response_model=SessionSummary | None)
async def active_session(user: CurrentUser, service: Service) -> SessionSummary | None:
    return await service.get_active(user)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, user: CurrentUser, service: Service) -> SessionDetail:
    return await service.get(user, session_id)


@router.post("/sessions/{session_id}/advance", response_model=SessionDetail)
async def advance(session_id: str, user: CurrentUser, service: Service) -> SessionDetail:
    return await service.advance(user, session_id)


@router.post("/sessions/{session_id}/switch", response_model=SessionDetail)
async def switch(
    session_id: str, data: SwitchStage, user: CurrentUser, service: Service
) -> SessionDetail:
    return await service.switch(user, session_id, data.stage)


@router.post("/sessions/{session_id}/finish", response_model=SessionDetail)
async def finish(session_id: str, user: CurrentUser, service: Service) -> SessionDetail:
    return await service.finish(user, session_id)


@router.post("/sessions/{session_id}/abandon", response_model=SessionDetail)
async def abandon(session_id: str, user: CurrentUser, service: Service) -> SessionDetail:
    return await service.abandon(user, session_id)


@router.get("/sessions/{session_id}/review", response_model=SessionReview)
async def review(session_id: str, user: CurrentUser, service: Service) -> SessionReview:
    return await service.review(user, session_id)
