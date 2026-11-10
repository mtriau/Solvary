import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import (
    check_execution_quota,
    get_current_user,
    get_member_repository,
    get_problem_repository,
    get_workspace_repository,
)
from app.api.sse import format_sse
from app.config import Settings, get_settings
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.problem import SUPPORTED_LANGUAGES
from app.models.user import User
from app.repositories.problem_repository import ProblemRepository
from app.repositories.workspace_repository import MemberRepository, WorkspaceRepository
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
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
) -> RunResponse:
    """Ad-hoc run — fire-and-watch; results are ephemeral (§6.5), graded
    history belongs to Submissions. With `workspace_id`, the caller must be
    an editor+ member of that workspace (design §5). With `problem_id` on a
    pytest-mode problem, the run executes the provided suite (stdin lists the
    test ids, blank = all) and reports printed output per test."""
    if data.language not in SUPPORTED_LANGUAGES:
        raise BadRequestException(
            f"Unsupported language '{data.language}' (supported: {', '.join(SUPPORTED_LANGUAGES)})"
        )
    if len(data.code.encode()) > settings.execution_max_code_bytes:
        raise BadRequestException(f"Code exceeds {settings.execution_max_code_bytes} bytes")

    if data.workspace_id:
        workspace = await workspace_repo.get_by_id(data.workspace_id)
        if not workspace:
            raise NotFoundException(f"Workspace {data.workspace_id} not found")
        member = await member_repo.get_by_workspace_and_user(data.workspace_id, current_user.id)
        if member is None or member.role == "viewer":
            raise ForbiddenException("Running code in a workspace requires editor access")

    harness = None
    time_limit_s = settings.execution_default_time_limit_s
    memory_kb = settings.execution_default_memory_kb
    if data.problem_id:
        problem = await problem_repo.get_by_id(data.problem_id)
        if not problem:
            raise NotFoundException(f"Problem {data.problem_id} not found")
        if problem.judge_mode == "pytest":
            if data.language != "python":
                raise BadRequestException("This problem is judged with a Python test suite")
            harness = problem.harness
            time_limit_s = problem.time_limit_s
            memory_kb = problem.memory_kb

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    job = ExecJob(
        id=run_id,
        user_id=current_user.id,
        language=data.language,
        code=data.code,
        mode="run",
        stdin=data.stdin,
        harness=harness,
        time_limit_s=time_limit_s,
        memory_kb=memory_kb,
    )
    # Register the run with the broker BEFORE enqueueing: the events
    # endpoint can then 404 unknown ids without racing the worker's first
    # event, and a subscriber that beats the worker still replays `queued`.
    await runtime.broker.publish(run_id, {"kind": "queued"})
    await runtime.queue.enqueue(job)
    return RunResponse(run_id=run_id)


@router.get("/{run_id}/events")
async def stream_run_events(
    run_id: str,
    _current_user: Annotated[User, Depends(get_current_user)],
    runtime: Annotated[ExecutionRuntime, Depends(get_runtime)],
) -> StreamingResponse:
    """SSE stream for an ad-hoc run: replays what the broker still holds,
    follows until terminal. Runs are ephemeral (§6.5) — after a restart or
    broker eviction the id is simply unknown (404)."""
    if not await runtime.broker.known(run_id):
        raise NotFoundException(f"Run {run_id} not found")

    async def event_stream():
        async for event in runtime.broker.subscribe(run_id):
            yield format_sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
