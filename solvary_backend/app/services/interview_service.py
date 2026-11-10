"""
Mock interviews (SOLVARY_INTERVIEWS_DESIGN.md).

Server-authoritative clock: every response carries started_at / ends_at /
server_time; expiry is LAZY (any touch past ends_at + grace finalizes the
session). Results are DERIVED from the submissions tagged with the session
id — the worker knows nothing about interviews. Code lives in a workspace
of kind "interview" (one file per stage in `questions`, one shared file in
`levels`), so a reload mid-interview loses nothing.

`utcnow` is a module attribute so tests can monkeypatch the clock.
"""

import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.interview import InterviewSession, InterviewStage, InterviewTemplate
from app.models.problem import SUPPORTED_LANGUAGES, Problem
from app.models.submission import Submission
from app.models.user import User
from app.repositories.interview_repository import (
    InterviewSessionRepository,
    InterviewStageRepository,
    InterviewTemplateRepository,
)
from app.repositories.problem_repository import ProblemRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.schemas.common import PaginatedResponse
from app.schemas.interviews import (
    Score,
    SessionDetail,
    SessionReview,
    SessionStart,
    SessionSummary,
    StageInfo,
    StageResult,
    StageView,
    TemplateCreate,
    TemplateDetail,
    TemplateInfo,
    TemplateSummary,
    TimelineEntry,
)
from app.schemas.problems import TestCaseSample
from app.services.problem_service import ProblemService
from app.services.submission_service import SubmissionService
from app.services.workspace_service import WorkspaceService

_EXT = {"python": "py", "javascript": "js"}


def _stage_filename(problem: Problem, default: str) -> str:
    """pytest problems import the candidate's code by module name, so name the file after it."""
    if problem.judge_mode == "pytest" and problem.harness and problem.harness.get("module"):
        return f"{problem.harness['module']}.py"
    return default


def utcnow() -> datetime:
    return datetime.now(UTC)


# ── pure helpers (also used by StatsService) ──────────────────────


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _parse(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def stage_times(timeline: list[dict], end: datetime) -> dict[int, float]:
    """Seconds spent per stage: each timeline entry is current until the
    next entry (or `end`)."""
    entries = sorted(((_parse(e["at"]), int(e["stage"])) for e in timeline), key=lambda e: e[0])
    spent: dict[int, float] = defaultdict(float)
    for i, (at, stage) in enumerate(entries):
        stop = entries[i + 1][0] if i + 1 < len(entries) else end
        spent[stage] += max(0.0, (stop - at).total_seconds())
    return dict(spent)


def best_per_problem(subs: list[Submission]) -> dict[str, Submission]:
    """Best submission per problem: max passed, ties → latest."""
    best: dict[str, Submission] = {}
    for s in sorted(subs, key=lambda s: (s.created_at, s.id)):
        cur = best.get(s.problem_id)
        if cur is None or s.passed >= cur.passed:
            best[s.problem_id] = s
    return best


def session_duration_s(session: InterviewSession) -> int:
    return int((session.ends_at - session.started_at).total_seconds())


def scaled_budgets(
    template: InterviewTemplate, stages: list[InterviewStage], session: InterviewSession
) -> dict[int, int | None]:
    """Stage budgets for THIS run: a session started with a different clock
    than its template scales every budget by the same ratio (60 of 90
    minutes → 15 min budget becomes 10)."""
    ratio = session_duration_s(session) / template.duration_s if template.duration_s else 1.0
    return {
        s.ordinal: None if s.budget_s is None else max(60, round(s.budget_s * ratio))
        for s in stages
    }


def stage_deadlines(
    template: InterviewTemplate,
    stages: list[InterviewStage],
    started_at: datetime,
    budgets: dict[int, int | None] | None = None,
) -> dict[int, datetime | None]:
    """Strict pacing: stage N's hard deadline = start + Σ budgets 1..N.
    None once a stage without a budget is hit (and for coached templates)."""
    out: dict[int, datetime | None] = {}
    if template.pacing != "strict":
        return {s.ordinal: None for s in stages}
    acc = 0
    broken = False
    for s in stages:
        budget = budgets[s.ordinal] if budgets is not None else s.budget_s
        if broken or budget is None:
            broken = True
            out[s.ordinal] = None
        else:
            acc += budget
            out[s.ordinal] = started_at + timedelta(seconds=acc)
    return out


def session_end(session: InterviewSession, now: datetime) -> datetime:
    if session.finished_at is not None:
        return session.finished_at
    return min(now, session.ends_at)


class InterviewService:
    def __init__(
        self,
        template_repo: InterviewTemplateRepository,
        stage_repo: InterviewStageRepository,
        session_repo: InterviewSessionRepository,
        problem_repo: ProblemRepository,
        testcase_repo: TestCaseRepository,
        submission_repo: SubmissionRepository,
        workspace_service: WorkspaceService,
        settings: Settings,
    ) -> None:
        self._templates = template_repo
        self._stages = stage_repo
        self._sessions = session_repo
        self._problems = problem_repo
        self._testcases = testcase_repo
        self._submissions = submission_repo
        self._workspaces = workspace_service
        self._settings = settings

    @property
    def _grace(self) -> timedelta:
        return timedelta(seconds=self._settings.interview_grace_s)

    # ── templates ──────────────────────────────────────────────────

    async def list_templates(self, user: User) -> list[TemplateSummary]:
        templates = await self._templates.list_public()
        mine = await self._sessions.list_by_user(user.id)
        out = []
        for t in templates:
            stages = await self._stages.list_by_template(t.id)
            out.append(await self._template_summary(t, stages, mine))
        return out

    async def get_template(self, user: User, slug: str) -> TemplateDetail:
        t = await self._templates.get_by_slug(slug)
        if not t or (not t.is_public and user.role != "admin"):
            raise NotFoundException(f"Interview '{slug}' not found")
        stages = await self._stages.list_by_template(t.id)
        mine = await self._sessions.list_by_user(user.id)
        summary = await self._template_summary(t, stages, mine)
        return TemplateDetail(**summary.model_dump(), description_md=t.description_md)

    async def create_template(self, admin: User, data: TemplateCreate) -> TemplateDetail:
        if await self._templates.get_by_slug(data.slug):
            raise ConflictException(f"An interview with slug '{data.slug}' already exists")
        seen: set[str] = set()
        for s in data.stages:
            if s.problem_id in seen:
                raise BadRequestException("A problem may appear only once per interview")
            seen.add(s.problem_id)
            if not await self._problems.get_by_id(s.problem_id):
                raise NotFoundException(f"Problem {s.problem_id} not found")

        template = InterviewTemplate(
            id=f"itpl_{uuid.uuid4().hex[:8]}",
            slug=data.slug,
            title=data.title,
            description_md=data.description_md,
            format=data.format,
            duration_s=data.duration_s,
            advance=data.advance,
            pacing=data.pacing,
            is_public=data.is_public,
            created_by=admin.id,
        )
        await self._templates.create(template)
        stages = []
        for i, s in enumerate(data.stages, start=1):
            stage = InterviewStage(
                id=f"istg_{uuid.uuid4().hex[:8]}",
                template_id=template.id,
                ordinal=i,
                problem_id=s.problem_id,
                title=s.title,
                budget_s=s.budget_s,
            )
            await self._stages.create(stage)
            stages.append(stage)
        summary = await self._template_summary(template, stages, [])
        return TemplateDetail(**summary.model_dump(), description_md=template.description_md)

    async def _template_summary(
        self, t: InterviewTemplate, stages: list[InterviewStage], mine: list[InterviewSession]
    ) -> TemplateSummary:
        past = [s for s in mine if s.template_id == t.id and s.status in ("finished", "expired")]
        last = max(past, key=lambda s: (s.created_at, s.id), default=None)
        last_result = await self._summary(last, t, stages) if last else None
        return TemplateSummary(
            **self._template_info(t).model_dump(),
            stages=[
                StageInfo(ordinal=s.ordinal, title=s.title, budget_s=s.budget_s) for s in stages
            ],
            last_result=last_result,
        )

    @staticmethod
    def _template_info(t: InterviewTemplate) -> TemplateInfo:
        return TemplateInfo(
            id=t.id,
            slug=t.slug,
            title=t.title,
            format=t.format,
            duration_s=t.duration_s,
            advance=t.advance,
            pacing=t.pacing,
        )

    # ── session lifecycle ──────────────────────────────────────────

    async def start(self, user: User, data: SessionStart) -> SessionDetail:
        template = await self._templates.get_by_id(data.template_id)
        if not template or (not template.is_public and user.role != "admin"):
            raise NotFoundException(f"Interview {data.template_id} not found")
        if data.language not in SUPPORTED_LANGUAGES:
            raise BadRequestException(f"Unsupported language '{data.language}'")
        stages = await self._stages.list_by_template(template.id)
        if not stages:
            raise BadRequestException("Interview has no stages")

        active = await self._sessions.get_active_for_user(user.id)
        if active:
            active_t = await self._templates.get_by_id(active.template_id)
            active_stages = await self._stages.list_by_template(active.template_id)
            if active_t:
                await self._touch(active, active_t, active_stages)
            if active.status == "active":
                raise ConflictException("An interview is already in progress")

        problems: list[Problem] = []
        for s in stages:
            p = await self._problems.get_by_id(s.problem_id)
            if not p:
                raise BadRequestException(f"Interview references a missing problem ({s.title})")
            problems.append(p)

        if data.language != "python" and any(p.judge_mode == "pytest" for p in problems):
            raise BadRequestException("This interview is Python-only (judged by a pytest suite)")

        ext = _EXT.get(data.language, "txt")
        if template.format == "levels":
            first = problems[0]
            files = [
                (_stage_filename(first, f"main.{ext}"), first.starter_code.get(data.language, ""))
            ]
        else:
            files = [
                (_stage_filename(p, f"q{s.ordinal}.{ext}"), p.starter_code.get(data.language, ""))
                for s, p in zip(stages, problems)
            ]
        workspace, file_ids = await self._workspaces.create_for_interview(
            user, template.title, data.language, files
        )
        if template.format == "levels":
            stage_files = {str(s.ordinal): file_ids[0] for s in stages}
        else:
            stage_files = {str(s.ordinal): fid for s, fid in zip(stages, file_ids)}

        now = utcnow()
        duration_s = data.duration_s or template.duration_s
        session = InterviewSession(
            id=f"isess_{uuid.uuid4().hex[:8]}",
            template_id=template.id,
            user_id=user.id,
            language=data.language,
            workspace_id=workspace.id,
            started_at=now,
            ends_at=now + timedelta(seconds=duration_s),
            current_stage=1,
            unlocked_through=1 if template.format == "levels" else len(stages),
            stage_files=stage_files,
            timeline=[{"stage": 1, "at": _iso(now)}],
            created_at=now,
            updated_at=now,
        )
        await self._sessions.create(session)
        return await self._detail(session, template, stages)

    async def get(self, user: User, session_id: str) -> SessionDetail:
        session, template, stages = await self._load(user, session_id)
        return await self._detail(session, template, stages)

    async def get_active(self, user: User) -> SessionSummary | None:
        session = await self._sessions.get_active_for_user(user.id)
        if not session:
            return None
        template, stages = await self._template_of(session)
        await self._touch(session, template, stages)
        if session.status != "active":
            return None
        return await self._summary(session, template, stages)

    async def list_mine(
        self, user: User, cursor: str | None = None, limit: int = 20
    ) -> PaginatedResponse[SessionSummary]:
        sessions, next_cursor = await self._sessions.list_paginated(user.id, cursor, limit)
        items = []
        for s in sessions:
            template, stages = await self._template_of(s)
            await self._touch(s, template, stages)
            items.append(await self._summary(s, template, stages))
        return PaginatedResponse(items=items, next_cursor=next_cursor)

    async def advance(self, user: User, session_id: str) -> SessionDetail:
        session, template, stages = await self._load(user, session_id)
        self._require_active(session)
        if template.format != "levels":
            raise ConflictException(
                "This interview has no parts to unlock; switch between questions instead"
            )
        if session.unlocked_through >= len(stages):
            raise ConflictException("Already on the last part")
        if template.advance != "free":
            results = await self._results(session, stages)
            current = results[session.current_stage]
            if template.advance == "on_submit" and current.submissions == 0:
                raise ConflictException("Submit this part at least once before moving on")
            if template.advance == "on_accept" and current.best_verdict != "accepted":
                raise ConflictException("Pass this part before moving on")
        self._do_advance(session, utcnow())
        await self._sessions.update(session)
        return await self._detail(session, template, stages)

    async def switch(self, user: User, session_id: str, stage: int) -> SessionDetail:
        session, template, stages = await self._load(user, session_id)
        self._require_active(session)
        if template.format != "questions":
            raise ConflictException("Level-based interviews only move forward; use advance")
        if not 1 <= stage <= len(stages):
            raise NotFoundException(f"No part {stage}")
        if stage > session.unlocked_through:
            raise ForbiddenException("This part is locked")
        if stage != session.current_stage:
            session.current_stage = stage
            session.timeline = [*session.timeline, {"stage": stage, "at": _iso(utcnow())}]
            await self._sessions.update(session)
        return await self._detail(session, template, stages)

    async def finish(self, user: User, session_id: str) -> SessionDetail:
        session, template, stages = await self._load(user, session_id)
        self._require_active(session)
        self._finalize(session, "finished", utcnow())
        await self._sessions.update(session)
        return await self._detail(session, template, stages)

    async def abandon(self, user: User, session_id: str) -> SessionDetail:
        session, template, stages = await self._load(user, session_id)
        self._require_active(session)
        self._finalize(session, "abandoned", utcnow())
        await self._sessions.update(session)
        return await self._detail(session, template, stages)

    async def review(self, user: User, session_id: str) -> SessionReview:
        session, template, stages = await self._load(user, session_id)
        if session.status == "active":
            raise ConflictException("The interview is still in progress")
        detail = await self._detail(session, template, stages, reveal_all=True)
        subs = await self._submissions.list_by_session(session.id)
        subs.sort(key=lambda s: (s.created_at, s.id))
        return SessionReview(
            **detail.model_dump(),
            submissions=[SubmissionService._to_response(s) for s in subs],
        )

    # ── hooks for other services ───────────────────────────────────

    async def authorize_submission(
        self, user: User, session_id: str, problem_id: str, workspace_id: str | None
    ) -> InterviewSession:
        """Called by SubmissionService: the session must be live, the
        problem must be an unlocked stage (levels: the current one)."""
        session, template, stages = await self._load(user, session_id)
        if session.user_id != user.id:
            raise ForbiddenException("Not your interview")
        if session.status == "expired":
            raise ConflictException("Interview time is up")
        if session.status != "active":
            raise ConflictException("The interview is over")
        now = utcnow()
        if now > session.ends_at + self._grace:
            raise ConflictException("Interview time is up")
        stage = next((s for s in stages if s.problem_id == problem_id), None)
        if stage is None:
            raise BadRequestException("Problem is not part of this interview")
        if stage.ordinal > session.unlocked_through:
            raise ForbiddenException("This part is locked")
        if template.format == "levels" and stage.ordinal != session.current_stage:
            raise ConflictException("Submissions target the current part")
        budgets = scaled_budgets(template, stages, session)
        deadline = stage_deadlines(template, stages, session.started_at, budgets)[stage.ordinal]
        if template.format == "questions" and deadline and now > deadline + self._grace:
            raise ConflictException("Time for this part is up")
        if workspace_id and workspace_id != session.workspace_id:
            raise BadRequestException("Workspace does not belong to this interview")
        return session

    async def problem_access(self, user: User, session_id: str, problem_id: str) -> bool:
        """AssistService: may the user get AI help on this problem via this
        session? Only after the session ended, and only for its stages."""
        session, _, stages = await self._load(user, session_id)
        if session.status == "active":
            raise ConflictException("AI help is disabled during an interview")
        return any(s.problem_id == problem_id for s in stages)

    async def has_active_session_with(self, user: User, problem_id: str) -> bool:
        session = await self._sessions.get_active_for_user(user.id)
        if not session:
            return False
        template, stages = await self._template_of(session)
        await self._touch(session, template, stages)
        return session.status == "active" and any(s.problem_id == problem_id for s in stages)

    # ── internals ──────────────────────────────────────────────────

    async def _template_of(
        self, session: InterviewSession
    ) -> tuple[InterviewTemplate, list[InterviewStage]]:
        template = await self._templates.get_by_id(session.template_id)
        if template is None:
            raise NotFoundException("Interview template no longer exists")
        return template, await self._stages.list_by_template(template.id)

    async def _load(
        self, user: User, session_id: str
    ) -> tuple[InterviewSession, InterviewTemplate, list[InterviewStage]]:
        session = await self._sessions.get_by_id(session_id)
        if not session:
            raise NotFoundException(f"Interview session {session_id} not found")
        if session.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Not your interview")
        template, stages = await self._template_of(session)
        await self._touch(session, template, stages)
        return session, template, stages

    async def _touch(
        self, session: InterviewSession, template: InterviewTemplate, stages: list[InterviewStage]
    ) -> None:
        """Lazy clock enforcement: expire past the deadline; under strict
        pacing in `levels`, auto-advance past elapsed stage budgets."""
        if session.status != "active":
            return
        now = utcnow()
        changed = False
        if template.pacing == "strict" and template.format == "levels":
            budgets = scaled_budgets(template, stages, session)
            deadlines = stage_deadlines(template, stages, session.started_at, budgets)
            while session.unlocked_through < len(stages):
                due = deadlines.get(session.current_stage)
                if due is None or now <= due:
                    break
                self._do_advance(session, due)
                changed = True
        if now > session.ends_at + self._grace:
            self._finalize(session, "expired", session.ends_at)
            changed = True
        if changed:
            await self._sessions.update(session)

    @staticmethod
    def _do_advance(session: InterviewSession, at: datetime) -> None:
        session.unlocked_through += 1
        session.current_stage = session.unlocked_through
        session.timeline = [*session.timeline, {"stage": session.current_stage, "at": _iso(at)}]

    @staticmethod
    def _finalize(session: InterviewSession, status: str, at: datetime) -> None:
        session.status = status  # type: ignore[assignment]
        session.finished_at = at

    @staticmethod
    def _require_active(session: InterviewSession) -> None:
        if session.status == "expired":
            raise ConflictException("Interview time is up")
        if session.status != "active":
            raise ConflictException("The interview is over")

    async def _results(
        self, session: InterviewSession, stages: list[InterviewStage]
    ) -> dict[int, StageResult]:
        subs = await self._submissions.list_by_session(session.id)
        by_problem: dict[str, list[Submission]] = defaultdict(list)
        for s in subs:
            by_problem[s.problem_id].append(s)
        best = best_per_problem(subs)
        spent = stage_times(session.timeline, session_end(session, utcnow()))

        out: dict[int, StageResult] = {}
        for stage in stages:
            b = best.get(stage.problem_id)
            if b is not None:
                total = b.total
            else:
                total = len(await self._testcases.list_by_problem(stage.problem_id))
            out[stage.ordinal] = StageResult(
                submissions=len(by_problem.get(stage.problem_id, [])),
                best_submission_id=b.id if b else None,
                best_verdict=b.verdict if b else None,
                best_passed=b.passed if b else 0,
                best_total=total,
                time_spent_s=int(spent.get(stage.ordinal, 0.0)),
            )
        return out

    @staticmethod
    def _score(results: dict[int, StageResult]) -> Score:
        passed = sum(r.best_passed for r in results.values())
        total = sum(r.best_total for r in results.values())
        percent = round(100 * passed / total) if total else 0
        return Score(passed=passed, total=total, percent=percent)

    @staticmethod
    def _diagnosis(
        stages: list[InterviewStage],
        results: dict[int, StageResult],
        session: InterviewSession,
        budgets: dict[int, int | None],
    ) -> str:
        parts: list[str] = []
        for s in stages:
            r = results[s.ordinal]
            reached = s.ordinal <= session.unlocked_through
            budget = budgets.get(s.ordinal)
            if budget and reached and r.time_spent_s > 1.5 * budget:
                parts.append(f"{s.title} took {r.time_spent_s / budget:.1f}× its budget")
        unreached = [s.title for s in stages if s.ordinal > session.unlocked_through]
        if unreached:
            parts.append(f"{', '.join(unreached)} never reached")
        untouched = [
            s.title
            for s in stages
            if s.ordinal <= session.unlocked_through and results[s.ordinal].submissions == 0
        ]
        if untouched and not unreached:
            parts.append(f"no submission on {', '.join(untouched)}")
        if parts:
            return "; ".join(parts) + "."
        if all(r.best_verdict == "accepted" for r in results.values()):
            return "Every part accepted inside its budget — this is the pace to keep."
        return "Pacing was on budget; the misses were on correctness, not time."

    async def _summary(
        self, session: InterviewSession, template: InterviewTemplate, stages: list[InterviewStage]
    ) -> SessionSummary:
        now = utcnow()
        results = await self._results(session, stages)
        end = session_end(session, now)
        budgets = scaled_budgets(template, stages, session)
        return SessionSummary(
            id=session.id,
            template=self._template_info(template),
            status=session.status,
            language=session.language,
            duration_s=session_duration_s(session),
            started_at=session.started_at,
            ends_at=session.ends_at,
            finished_at=session.finished_at,
            server_time=now,
            score=self._score(results),
            time_used_s=int(max(0.0, (end - session.started_at).total_seconds())),
            stages_reached=session.unlocked_through,
            stage_count=len(stages),
            diagnosis=(
                None
                if session.status == "active"
                else self._diagnosis(stages, results, session, budgets)
            ),
        )

    async def _detail(
        self,
        session: InterviewSession,
        template: InterviewTemplate,
        stages: list[InterviewStage],
        reveal_all: bool = False,
    ) -> SessionDetail:
        summary = await self._summary(session, template, stages)
        results = await self._results(session, stages)
        budgets = scaled_budgets(template, stages, session)
        deadlines = stage_deadlines(template, stages, session.started_at, budgets)
        views = []
        for stage in stages:
            unlocked = reveal_all or stage.ordinal <= session.unlocked_through
            problem_detail = None
            editorial = None
            if unlocked:
                problem = await self._problems.get_by_id(stage.problem_id)
                if problem is not None:
                    cases = await self._testcases.list_by_problem(problem.id)
                    samples = [
                        TestCaseSample(
                            ordinal=c.ordinal, stdin=c.stdin, expected_stdout=c.expected_stdout
                        )
                        for c in cases
                        if c.is_sample
                    ]
                    problem_detail = ProblemService._to_detail(problem, samples)
                    if reveal_all:
                        editorial = problem.editorial_md
            views.append(
                StageView(
                    ordinal=stage.ordinal,
                    title=stage.title,
                    budget_s=budgets[stage.ordinal],
                    locked=not unlocked,
                    file_id=session.stage_files.get(str(stage.ordinal)) if unlocked else None,
                    deadline_at=deadlines.get(stage.ordinal),
                    problem=problem_detail,
                    editorial_md=editorial,
                    result=results[stage.ordinal],
                )
            )
        return SessionDetail(
            **summary.model_dump(),
            workspace_id=session.workspace_id,
            current_stage=session.current_stage,
            unlocked_through=session.unlocked_through,
            stages=views,
            timeline=[
                TimelineEntry(stage=e["stage"], at=_parse(e["at"])) for e in session.timeline
            ],
        )
