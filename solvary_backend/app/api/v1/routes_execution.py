import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import check_execution_quota, get_current_user
from app.api.sse import format_sse
from app.config import Settings, get_settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.problem import SUPPORTED_LANGUAGES
from app.models.user import User
from app.schemas.execution import RunRequest, RunResponse
from app.services.execution.base import ExecJob
from app.services.queue.runtime import ExecutionRuntime, get_runtime

router = APIRouter(prefix="/v1/execution", tags=["execution"])


@router.post("/run", response_model=RunResponse, dependencies=[Depends(check_execution_quota)])
async def run_code(
    data: RunRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    runtime: Annotated[ExecutionRuntime, Depends(get_runtime)],
) -> RunResponse:
    """Ad-hoc run — fire-and-watch; results are ephemeral (§6.5), graded
    history belongs to Submissions. `workspace_id` RBAC check arrives with
    workspaces in M3."""
    if data.language not in SUPPORTED_LANGUAGES:
        raise BadRequestException(
            f"Unsupported language '{data.language}' (supported: {', '.join(SUPPORTED_LANGUAGES)})"
        )
    if len(data.code.encode()) > settings.execution_max_code_bytes:
        raise BadRequestException(f"Code exceeds {settings.execution_max_code_bytes} bytes")

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    job = ExecJob(
        id=run_id,
        user_id=current_user.id,
        language=data.language,
        code=data.code,
        mode="run",
        stdin=data.stdin,
        time_limit_s=settings.execution_default_time_limit_s,
        memory_kb=settings.execution_default_memory_kb,
    )
    await runtime.queue.enqueue(job)
    return RunResponse(run_id=run_id)


@router.get("/{run_id}/events")
async def stream_run_events(
    run_id: str,
    _current_user: Annotated[User, Depends(get_current_user)],
    runtime: Annotated[ExecutionRuntime, Depends(get_runtime)],
) -> StreamingResponse:
    """SSE stream for an ad-hoc run. In-memory only: replays what the broker
    still holds, follows until terminal; lost on restart (§6.5)."""
    if not await runtime.broker.known(run_id) and await runtime.broker.is_done(run_id):
        raise NotFoundException(f"Run {run_id} not found")

    async def event_stream():
        async for event in runtime.broker.subscribe(run_id):
            yield format_sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
