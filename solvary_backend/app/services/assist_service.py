"""
AI assistant (design §5 `POST /v1/assist/explain`, decision #12).

Builds a tutoring prompt from the problem statement, the user's current
code, and (optionally) the verdict they just got, then streams the LLM's
reply as SSE frames: {"content": "..."} chunks followed by {"done": true}.
Hidden test cases are never included — only what the user can already see.
"""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from app.config import Settings
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.user import User
from app.repositories.problem_repository import ProblemRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.schemas.assist import AssistRequest
from app.services.llm_service import BaseLLMService, ChatMessage

if TYPE_CHECKING:
    from app.services.interview_service import InterviewService

_MAX_QUESTION_CHARS = 2000


class AssistService:
    def __init__(
        self,
        problem_repo: ProblemRepository,
        testcase_repo: TestCaseRepository,
        llm: BaseLLMService,
        settings: Settings,
        interview_service: "InterviewService | None" = None,
    ) -> None:
        self._problems = problem_repo
        self._testcases = testcase_repo
        self._llm = llm
        self._settings = settings
        self._interviews = interview_service

    async def build_messages(
        self, data: AssistRequest, user: User | None = None
    ) -> list[ChatMessage]:
        if len(data.question) > _MAX_QUESTION_CHARS:
            raise BadRequestException(f"Question exceeds {_MAX_QUESTION_CHARS} characters")
        if data.code and len(data.code.encode()) > self._settings.execution_max_code_bytes:
            raise BadRequestException(
                f"Code exceeds {self._settings.execution_max_code_bytes} bytes"
            )

        parts: list[str] = []
        if data.problem_id:
            problem = await self._problems.get_by_id(data.problem_id)
            # Mock interviews: no AI help while one is running; afterwards the
            # session authorizes its own (private) stage problems for review
            allowed = problem is not None and problem.is_public
            if problem is not None and self._interviews is not None and user is not None:
                if data.interview_session_id:
                    allowed = await self._interviews.problem_access(
                        user, data.interview_session_id, problem.id
                    )
                elif allowed and await self._interviews.has_active_session_with(
                    user, problem.id
                ):
                    raise ConflictException("AI help is disabled during an interview")
            if not allowed:
                raise NotFoundException(f"Problem {data.problem_id} not found")
            parts.append(
                f"## Problem: {problem.title} ({problem.difficulty})\n\n{problem.statement_md}"
            )
            samples = [
                c for c in await self._testcases.list_by_problem(problem.id) if c.is_sample
            ]
            if samples:
                shown = "\n\n".join(
                    f"Sample {c.ordinal} input:\n```\n{c.stdin}```\nexpected output:\n"
                    f"```\n{c.expected_stdout}```"
                    for c in samples
                )
                parts.append(f"## Sample tests\n\n{shown}")

        if data.code and data.code.strip():
            lang = data.language or ""
            parts.append(f"## My current code\n\n```{lang}\n{data.code}\n```")
        if data.verdict:
            parts.append(f"## Latest judge verdict\n\n{data.verdict}")
        parts.append(f"## Question\n\n{data.question.strip()}")

        return [
            ChatMessage(role="system", content=self._settings.llm_system_prompt),
            ChatMessage(role="user", content="\n\n".join(parts)),
        ]

    async def stream_reply(self, messages: list[ChatMessage]) -> AsyncIterator[dict]:
        """SSE payloads: {"content": str}* then {"done": true}."""
        async for chunk in self._llm.stream_response(messages):
            if chunk.done:
                yield {"done": True}
                return
            if chunk.content:
                yield {"content": chunk.content}
        yield {"done": True}

    async def stream_explain(self, data: AssistRequest) -> AsyncIterator[dict]:
        messages = await self.build_messages(data)
        async for payload in self.stream_reply(messages):
            yield payload
