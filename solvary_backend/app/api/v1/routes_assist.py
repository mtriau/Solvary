from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_assist_service, get_current_user
from app.api.sse import format_sse
from app.core.rate_limit import assist_limiter
from app.models.user import User
from app.schemas.assist import AssistRequest
from app.services.assist_service import AssistService

router = APIRouter(prefix="/v1/assist", tags=["assist"])


@router.post("/explain")
async def explain(
    data: AssistRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AssistService, Depends(get_assist_service)],
) -> StreamingResponse:
    """SSE: `{"content": "..."}` chunks, then `{"done": true}`."""
    await assist_limiter.check(current_user.id)
    # Validate (404/400) before the stream starts — errors inside a
    # StreamingResponse body can't change the status code
    messages = await service.build_messages(data, current_user)

    async def event_stream():
        async for payload in service.stream_reply(messages):
            yield format_sse(payload)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
