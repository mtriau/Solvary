"""
Interviewer agent (SOLVARY_INTERVIEWER_DESIGN.md).

A *turn* is one request to Claude and one streamed reply. `prepare_turn`
validates and assembles the prompt (so every 4xx happens before the SSE
response starts); `stream_turn` holds the per-session lock, streams the
reply as `{"content"}` frames, detects the `[silent]` protocol, persists the
user turn and the reply, and ends with a `{"done": true, …}` frame.

Persistence happens from inside the stream, after the request's own DB
session may already be gone, so writes go through `open_turn_repo`, a
factory that yields a repository on a fresh session (or the mock repo).
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.config import Settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    PaymentRequiredException,
)
from app.models.interview import InterviewSession, InterviewStage, InterviewTemplate
from app.models.interviewer import REFUSED, SILENT, InterviewerTurn
from app.models.problem import Problem
from app.models.testcase import TestCase
from app.models.user import User
from app.repositories.interviewer_repository import InterviewerTurnRepository
from app.repositories.problem_repository import ProblemRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.schemas.interviewer import (
    InterviewerTranscript,
    InterviewerTurnRequest,
    InterviewerTurnResponse,
)
from app.services import interview_service as iv
from app.services.ai_keys import resolve_api_key
from app.services.claude_client import ClaudeClient, ClaudeError
from app.services.interview_service import InterviewService
from app.services.interviewer_prompt import (
    STATIC_SYSTEM,
    Truth,
    digest,
    history_user_text,
    render_screen,
    render_template_package,
)

logger = logging.getLogger(__name__)

OpenTurnRepo = Callable[[], AbstractAsyncContextManager[InterviewerTurnRepository]]

# One in-flight turn per session (single-instance, like the memory limiter)
_locks: dict[str, asyncio.Lock] = {}
_LOCK_WAIT_S = 90.0


def _lock_for(session_id: str) -> asyncio.Lock:
    lock = _locks.get(session_id)
    if lock is None:
        lock = _locks[session_id] = asyncio.Lock()
    return lock


def _new_id() -> str:
    return f"ivt_{uuid.uuid4().hex[:8]}"


@dataclass
class PreparedTurn:
    user: User
    session_id: str
    request: InterviewerTurnRequest
    api_key: str
    system: list[dict]
    messages: list[dict]
    user_content: str  # what gets stored for the user turn
    digest: str
    model: str
    effort: str
    max_tokens: int
    screen_text: str = field(repr=False, default="")


class InterviewerService:
    def __init__(
        self,
        turn_repo: InterviewerTurnRepository,
        open_turn_repo: OpenTurnRepo,
        interview_service: InterviewService,
        problem_repo: ProblemRepository,
        testcase_repo: TestCaseRepository,
        claude: ClaudeClient,
        settings: Settings,
    ) -> None:
        self._turns = turn_repo
        self._open_turn_repo = open_turn_repo
        self._interviews = interview_service
        self._problems = problem_repo
        self._testcases = testcase_repo
        self._claude = claude
        self._settings = settings

    # ── reads ──────────────────────────────────────────────────────

    async def list_turns(self, user: User, session_id: str) -> InterviewerTranscript:
        session, _, _ = await self._interviews.load_for_agent(user, session_id)
        turns = await self._turns.list_by_session(session.id)
        _, source = resolve_api_key(user, self._settings)
        return InterviewerTranscript(
            turns=[self.to_response(t) for t in turns],
            idle_s=self._settings.interviewer_idle_s,
            model=self._settings.interviewer_model,
            key_source=source,
            active=session.status == "active",
        )

    async def clear(self, user: User, session_id: str) -> int:
        session, _, _ = await self._interviews.load_for_agent(user, session_id)
        if session.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Not your interview")
        return await self._turns.delete_by_session(session.id)

    @staticmethod
    def to_response(t: InterviewerTurn) -> InterviewerTurnResponse:
        return InterviewerTurnResponse(
            id=t.id,
            ordinal=t.ordinal,
            role=t.role,
            trigger=t.trigger,
            content=t.content,
            digest=t.digest,
            silent=t.silent,
            model=t.model,
            input_tokens=t.input_tokens,
            output_tokens=t.output_tokens,
            cache_read_input_tokens=t.cache_read_input_tokens,
            cache_creation_input_tokens=t.cache_creation_input_tokens,
            created_at=t.created_at,
        )

    # ── a turn ─────────────────────────────────────────────────────

    async def prepare_turn(
        self, user: User, session_id: str, req: InterviewerTurnRequest
    ) -> PreparedTurn:
        session, template, stages = await self._interviews.load_for_agent(user, session_id)
        if session.user_id != user.id:
            raise ForbiddenException("Not your interview")
        if session.status == "expired":
            raise ConflictException("Interview time is up")
        if session.status != "active":
            raise ConflictException("The interview is over")
        if len(req.screen.code.encode()) > self._settings.execution_max_code_bytes:
            raise BadRequestException(
                f"Code exceeds {self._settings.execution_max_code_bytes} bytes"
            )
        if not any(s.ordinal == req.screen.stage for s in stages):
            raise BadRequestException(f"No part {req.screen.stage}")
        if _lock_for(session.id).locked():
            raise ConflictException("A turn is already in progress")

        api_key, _ = resolve_api_key(user, self._settings)
        if not api_key:
            raise PaymentRequiredException(
                "No Anthropic API key configured. Add yours under Interviews -> Interviewer."
            )

        problems, cases = await self._load_problems(stages)
        package = render_template_package(
            template, stages, problems, cases, self._settings.interviewer_knows_solutions
        )
        results = await self._interviews.results_for(session, stages)
        truth = self._truth(session, template, stages, problems, results)

        history, unanswered = await self._history(session.id)
        events = list(req.events)
        if unanswered is not None:
            events.append(f"earlier, unanswered (your reply never arrived): {unanswered.content}")
        utterance = req.utterance.strip() if req.utterance else None
        screen_text = render_screen(truth, req.screen, events, utterance)
        messages = history + [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": screen_text, "cache_control": {"type": "ephemeral"}}
                ],
            }
        ]
        system = [
            {"type": "text", "text": STATIC_SYSTEM},
            {"type": "text", "text": package, "cache_control": {"type": "ephemeral"}},
        ]
        stored = utterance or ""
        if req.events:
            event_text = "\n".join(f"[event] {e}" for e in req.events)
            stored = f"{event_text}\n{stored}".strip() if stored else event_text
        if not stored:
            opening = req.trigger == "opening"
            stored = "[event] The interview has started." if opening else "(no speech)"

        return PreparedTurn(
            user=user,
            session_id=session.id,
            request=req,
            api_key=api_key,
            system=system,
            messages=messages,
            user_content=stored,
            digest=digest(truth, req.screen),
            model=self._settings.interviewer_model,
            effort=self._settings.interviewer_effort,
            max_tokens=self._settings.interviewer_max_tokens,
            screen_text=screen_text,
        )

    async def stream_turn(self, prepared: PreparedTurn) -> AsyncIterator[dict]:
        """SSE payloads: {"content": str}* then {"done": true, "spoke": bool, …};
        or {"error": str} then a done frame with "error": true."""
        lock = _lock_for(prepared.session_id)
        try:
            await asyncio.wait_for(lock.acquire(), timeout=_LOCK_WAIT_S)
        except TimeoutError:
            yield {"error": "A turn is already in progress"}
            yield {"done": True, "spoke": False, "error": True}
            return
        try:
            async for payload in self._run(prepared):
                yield payload
        finally:
            lock.release()

    async def _run(self, p: PreparedTurn) -> AsyncIterator[dict]:
        reply = ""
        pending = ""  # held back until we know whether the reply is [silent]
        decided = False
        silent = False
        final = None
        try:
            async for chunk in self._claude.stream_turn(
                p.api_key,
                p.system,
                p.messages,
                model=p.model,
                effort=p.effort,
                max_tokens=p.max_tokens,
            ):
                if chunk.done:
                    final = chunk
                    break
                if not chunk.text:
                    continue
                if decided:
                    reply += chunk.text
                    if not silent:
                        yield {"content": chunk.text}
                    continue
                pending += chunk.text
                head = pending.lstrip()
                if len(head) < len(SILENT) and SILENT.startswith(head):
                    continue  # could still become "[silent]"
                decided = True
                silent = head.startswith(SILENT)
                reply = pending
                if not silent:
                    yield {"content": pending}
        except ClaudeError as e:
            logger.warning("interviewer turn failed for %s: %s", p.session_id, e.detail)
            yield {"error": e.detail}
            yield {"done": True, "spoke": False, "error": True, "status": e.status}
            return

        if not decided:
            reply = pending
            head = pending.strip()
            silent = head == "" or SILENT.startswith(head)
            if not silent:
                yield {"content": pending}

        stop_reason = final.stop_reason if final else None
        refused = stop_reason == "refusal"
        truncated = stop_reason == "max_tokens"
        if refused:
            silent = False
            reply = REFUSED
            yield {"error": "The interviewer declined to answer that."}
        elif silent or not reply.strip():
            silent = True
            reply = SILENT

        usage = final.usage if final else {}
        now = datetime.now(UTC)
        async with self._open_turn_repo() as repo:
            ordinal = await repo.next_ordinal(p.session_id)
            user_turn = InterviewerTurn(
                id=_new_id(),
                session_id=p.session_id,
                user_id=p.user.id,
                ordinal=ordinal,
                role="user",
                trigger=p.request.trigger,
                content=p.user_content,
                digest=p.digest,
                created_at=now,
            )
            assistant_turn = InterviewerTurn(
                id=_new_id(),
                session_id=p.session_id,
                user_id=p.user.id,
                ordinal=ordinal + 1,
                role="assistant",
                content=reply.strip(),
                silent=silent,
                model=(final.model if final and final.model else p.model),
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                cache_read_input_tokens=usage.get("cache_read_input_tokens"),
                cache_creation_input_tokens=usage.get("cache_creation_input_tokens"),
                created_at=now,
            )
            await repo.create(user_turn)
            await repo.create(assistant_turn)

        yield {
            "done": True,
            "spoke": not silent and not refused,
            "refused": refused,
            "truncated": truncated,
            "turn_id": assistant_turn.id,
            "user_turn_id": user_turn.id,
            "model": assistant_turn.model,
            "usage": usage,
        }

    # ── internals ──────────────────────────────────────────────────

    async def _load_problems(
        self, stages: list[InterviewStage]
    ) -> tuple[dict[str, Problem], dict[str, list[TestCase]]]:
        problems: dict[str, Problem] = {}
        cases: dict[str, list[TestCase]] = {}
        for s in stages:
            p = await self._problems.get_by_id(s.problem_id)
            if p is None:
                continue
            problems[p.id] = p
            cases[p.id] = await self._testcases.list_by_problem(p.id)
        return problems, cases

    @staticmethod
    def _truth(
        session: InterviewSession,
        template: InterviewTemplate,
        stages: list[InterviewStage],
        problems: dict[str, Problem],
        results,
    ) -> Truth:
        now = iv.utcnow()
        budgets = iv.scaled_budgets(template, stages, session)
        current = next((s for s in stages if s.ordinal == session.current_stage), stages[0])
        last = session.timeline[-1] if session.timeline else None
        elapsed = int((now - iv._parse(last["at"])).total_seconds()) if last else 0
        problem = problems.get(current.problem_id)
        harness_files = {}
        if problem is not None and problem.judge_mode == "pytest" and problem.harness:
            files = problem.harness.get("files") or {}
            harness_files = {name: len(src.encode()) for name, src in files.items()}
        return Truth(
            template_title=template.title,
            format=template.format,
            status=session.status,
            language=session.language,
            remaining_s=max(0, int((session.ends_at - now).total_seconds())),
            current_stage=session.current_stage,
            unlocked_through=session.unlocked_through,
            stage_count=len(stages),
            stage_title=current.title,
            stage_budget_s=budgets.get(current.ordinal),
            stage_elapsed_s=max(0, elapsed),
            results=results,
            stage_titles={s.ordinal: s.title for s in stages},
            harness_files=harness_files,
        )

    async def _history(self, session_id: str) -> tuple[list[dict], InterviewerTurn | None]:
        """Stored turns as model messages (digest + words for user turns,
        text for assistant turns). A trailing user turn with no reply is
        returned separately so the caller folds it into the new turn."""
        turns = await self._turns.list_by_session(session_id)
        unanswered = None
        if turns and turns[-1].role == "user":
            unanswered = turns.pop()
        messages: list[dict] = []
        for t in turns:
            if t.role == "user":
                text = history_user_text(t.digest, t.content)
                if messages and messages[-1]["role"] == "user":
                    messages[-1]["content"] += "\n\n" + text
                else:
                    messages.append({"role": "user", "content": text})
            else:
                content = t.content.strip() or SILENT
                if messages and messages[-1]["role"] == "assistant":
                    messages[-1]["content"] += "\n\n" + content
                elif not messages:
                    continue  # history must start with a user turn
                else:
                    messages.append({"role": "assistant", "content": content})
        if messages and messages[-1]["role"] == "user":
            # only happens if the orphan was not the very last row; fold it too
            orphan = messages.pop()
            if unanswered is None:
                unanswered = InterviewerTurn(
                    id="",
                    session_id=session_id,
                    user_id="",
                    ordinal=0,
                    role="user",
                    content=orphan["content"],
                )
        return messages, unanswered
