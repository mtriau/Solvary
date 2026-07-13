from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    check_execution_quota,
    get_current_user,
    get_submission_service,
)
from app.api.sse import format_sse
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.submissions import SubmissionCreate, SubmissionDetail, SubmissionResponse
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/v1/submissions", tags=["submissions"])


@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=201,
    dependencies=[Depends(check_execution_quota)],
)
async def create_submission(
    data: SubmissionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionResponse:
    return await service.create(current_user, data)


@router.get("", response_model=PaginatedResponse[SubmissionResponse])
async def list_submissions(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
    problem_id: str | None = None,
    workspace_id: str | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PaginatedResponse[SubmissionResponse]:
    if workspace_id:
        # Shared attempt history: every member's submissions (M4)
        return await service.list_for_workspace(
            current_user, workspace_id, cursor=cursor, limit=limit
        )
    return await service.list_mine(
        current_user, problem_id=problem_id, cursor=cursor, limit=limit
    )


@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> SubmissionDetail:
    return await service.get(current_user, submission_id)


@router.get("/{submission_id}/events")
async def stream_submission_events(
    submission_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubmissionService, Depends(get_submission_service)],
) -> StreamingResponse:
    """SSE stream: replay persisted progress, then follow live judge events."""

    async def event_stream():
        async for event in service.stream_events(current_user, submission_id):
            yield format_sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
