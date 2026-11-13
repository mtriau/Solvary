from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db, get_interviewer_service
from app.api.sse import format_sse
from app.core.rate_limit import interviewer_limiter
from app.models.user import User
from app.schemas.interviewer import InterviewerTranscript, InterviewerTurnRequest
from app.services.interviewer_service import InterviewerService

router = APIRouter(prefix="/v1/interviews/sessions/{session_id}/interviewer", tags=["interviewer"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[InterviewerService, Depends(get_interviewer_service)]


@router.get("/turns", response_model=InterviewerTranscript)
async def list_turns(session_id: str, user: CurrentUser, service: Service) -> InterviewerTranscript:
    """The transcript (oldest first) plus the client-facing agent settings."""
    return await service.list_turns(user, session_id)


@router.post("/turns")
async def post_turn(
    session_id: str,
    data: InterviewerTurnRequest,
    user: CurrentUser,
    service: Service,
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> StreamingResponse:
    """SSE: `{"content": "..."}` chunks, then `{"done": true, "spoke": bool, …}`;
    or `{"error": "..."}` followed by a done frame."""
    await interviewer_limiter.check(user.id)
    # Validate + assemble the prompt BEFORE the stream starts — errors inside
    # a StreamingResponse body can't change the status code (402/409/400…)
    prepared = await service.prepare_turn(user, session_id, data)
    if db is not None:
        # Release any pending write (lazy expiry / auto-advance) so the
        # stream's own session is never blocked behind this one on SQLite
        await db.commit()

    async def event_stream():
        async for payload in service.stream_turn(prepared):
            yield format_sse(payload)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/turns", status_code=204)
async def clear_turns(session_id: str, user: CurrentUser, service: Service) -> Response:
    """Wipe the transcript (owner or admin; testing aid, not in the UI)."""
    await service.clear(user, session_id)
    return Response(status_code=204)
