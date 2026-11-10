"""
Profile stats + accolades, computed live from submission history.

Badges are pure derivations (no persistence): once the criteria hold they
stay earned, because history only grows. Timezone note: streaks and the
heatmap bucket by UTC calendar day.
"""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from app.models.problem import SUPPORTED_LANGUAGES
from app.models.submission import Submission
from app.models.user import User
from app.repositories.interview_repository import (
    InterviewSessionRepository,
    InterviewStageRepository,
    InterviewTemplateRepository,
)
from app.repositories.problem_repository import ProblemRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.workspace_repository import MemberRepository
from app.schemas.stats import (
    Badge,
    DifficultyStat,
    HeatmapDay,
    LanguageStat,
    RecentSubmission,
    StatsResponse,
    TotalsStats,
)

_HEATMAP_DAYS = 182  # ~26 weeks
_RECENT = 10


def _utc_day(dt: datetime) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).date()


def _streaks(accepted_days: set[date]) -> tuple[int, int]:
    """(current, longest) runs of consecutive UTC days with an accept."""
    if not accepted_days:
        return 0, 0
    days = sorted(accepted_days)
    longest = run = 1
    for prev, cur in zip(days, days[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)

    today = datetime.now(UTC).date()
    current = 0
    # A streak is alive if it reaches today or yesterday
    probe = today if today in accepted_days else today - timedelta(days=1)
    while probe in accepted_days:
        current += 1
        probe -= timedelta(days=1)
    return current, longest


class StatsService:
    def __init__(
        self,
        submission_repo: SubmissionRepository,
        problem_repo: ProblemRepository,
        member_repo: MemberRepository,
        session_repo: InterviewSessionRepository | None = None,
        stage_repo: InterviewStageRepository | None = None,
        template_repo: InterviewTemplateRepository | None = None,
    ) -> None:
        self._submissions = submission_repo
        self._problems = problem_repo
        self._members = member_repo
        self._sessions = session_repo
        self._stages = stage_repo
        self._templates = template_repo

    async def compute(self, user: User) -> StatsResponse:
        subs = await self._submissions.list_by_user(user.id)
        subs.sort(key=lambda s: s.created_at)
        problems = [p for p in await self._problems.list_all() if p.is_public]
        problem_by_id = {p.id: p for p in problems}

        accepted = [s for s in subs if s.verdict == "accepted"]
        solved_ids = {s.problem_id for s in accepted if s.problem_id in problem_by_id}

        # ── difficulty breakdown ───────────────────────────────────
        by_difficulty = []
        for difficulty in ("easy", "medium", "hard"):
            pool = [p for p in problems if p.difficulty == difficulty]
            by_difficulty.append(
                DifficultyStat(
                    difficulty=difficulty,
                    solved=sum(1 for p in pool if p.id in solved_ids),
                    total=len(pool),
                )
            )

        # ── languages ──────────────────────────────────────────────
        lang_subs: dict[str, int] = defaultdict(int)
        lang_solved: dict[str, set[str]] = defaultdict(set)
        for s in subs:
            lang_subs[s.language] += 1
            if s.verdict == "accepted":
                lang_solved[s.language].add(s.problem_id)
        by_language = [
            LanguageStat(
                language=lang,
                submissions=lang_subs.get(lang, 0),
                solved=len(lang_solved.get(lang, set())),
            )
            for lang in SUPPORTED_LANGUAGES
            if lang_subs.get(lang)
        ]

        # ── streaks + heatmap ──────────────────────────────────────
        accepted_days = {_utc_day(s.created_at) for s in accepted}
        current_streak, longest_streak = _streaks(accepted_days)

        per_day: dict[date, int] = defaultdict(int)
        for s in subs:
            per_day[_utc_day(s.created_at)] += 1
        today = datetime.now(UTC).date()
        heatmap = [
            HeatmapDay(day=d, count=per_day.get(d, 0))
            for d in (
                today - timedelta(days=offset)
                for offset in range(_HEATMAP_DAYS - 1, -1, -1)
            )
        ]

        # ── recent activity ────────────────────────────────────────
        recent = []
        for s in reversed(subs[-_RECENT * 3:]):  # skip subs to deleted problems
            problem = problem_by_id.get(s.problem_id)
            if problem is None:
                continue
            recent.append(
                RecentSubmission(
                    id=s.id,
                    problem_slug=problem.slug,
                    problem_title=problem.title,
                    difficulty=problem.difficulty,
                    language=s.language,
                    verdict=s.verdict,
                    runtime_ms=s.runtime_ms,
                    created_at=s.created_at,
                )
            )
            if len(recent) == _RECENT:
                break

        badges = await self._badges(user, subs, accepted, solved_ids, problems)

        total_subs = len(subs)
        return StatsResponse(
            totals=TotalsStats(
                solved=len(solved_ids),
                total_problems=len(problems),
                submissions=total_subs,
                accepted_submissions=len(accepted),
                acceptance_rate=len(accepted) / total_subs if total_subs else 0.0,
                current_streak_days=current_streak,
                longest_streak_days=longest_streak,
            ),
            by_difficulty=by_difficulty,
            by_language=by_language,
            heatmap=heatmap,
            badges=badges,
            recent=recent,
        )

    # ── accolades ──────────────────────────────────────────────────

    async def _badges(
        self,
        user: User,
        subs: list[Submission],
        accepted: list[Submission],
        solved_ids: set[str],
        problems: list,
    ) -> list[Badge]:
        # Attempt order per problem → "first try" and "comeback" detection
        attempts: dict[str, list[str]] = defaultdict(list)
        for s in subs:
            attempts[s.problem_id].append(s.verdict)

        def first_try() -> bool:
            return any(v and v[0] == "accepted" for v in attempts.values())

        def comeback() -> bool:
            for verdicts in attempts.values():
                if "accepted" in verdicts:
                    fails_before = verdicts.index("accepted")
                    if fails_before >= 5:
                        return True
            return False

        langs_accepted = {s.language for s in accepted}
        _, longest_streak = _streaks({_utc_day(s.created_at) for s in accepted})

        collaborative = False
        memberships = await self._members.list_by_user(user.id)
        for m in memberships:
            others = await self._members.list_by_workspace(m.workspace_id)
            if len(others) >= 2:
                collaborative = True
                break

        total = len(subs)
        rate = len(accepted) / total if total else 0.0
        clock_beater, pacer = await self._interview_badges(user, subs)

        return [
            Badge(
                id="first-blood", name="First Blood", icon="🩸",
                description="Get your first Accepted verdict",
                earned=bool(accepted),
            ),
            Badge(
                id="one-shot", name="One Shot", icon="🎯",
                description="Solve a problem on your very first attempt",
                earned=first_try(),
            ),
            Badge(
                id="hat-trick", name="Hat Trick", icon="🎩",
                description="Accepted on 3 consecutive days",
                earned=longest_streak >= 3,
            ),
            Badge(
                id="week-warrior", name="Week Warrior", icon="🗓️",
                description="Accepted on 7 consecutive days",
                earned=longest_streak >= 7,
            ),
            Badge(
                id="polyglot", name="Polyglot", icon="🌐",
                description="Accepted in every supported language",
                earned=set(SUPPORTED_LANGUAGES) <= langs_accepted,
            ),
            Badge(
                id="sharpshooter", name="Sharpshooter", icon="🏹",
                description="80%+ acceptance across 10+ submissions",
                earned=total >= 10 and rate >= 0.8,
            ),
            Badge(
                id="century", name="Century", icon="💯",
                description="Make 100 submissions",
                earned=total >= 100,
            ),
            Badge(
                id="comeback-kid", name="Comeback Kid", icon="🔁",
                description="Crack a problem after 5+ failed attempts",
                earned=comeback(),
            ),
            Badge(
                id="night-owl", name="Night Owl", icon="🦉",
                description="Submit between midnight and 5am (UTC)",
                earned=any(0 <= _hour_utc(s.created_at) < 5 for s in subs),
            ),
            Badge(
                id="speed-demon", name="Speed Demon", icon="⚡",
                description="Accepted with a max case runtime under 50ms",
                earned=any(
                    s.runtime_ms is not None and s.runtime_ms < 50 for s in accepted
                ),
            ),
            Badge(
                id="pair-programmer", name="Pair Programmer", icon="🤝",
                description="Submit from a shared workspace",
                earned=any(s.workspace_id for s in subs),
            ),
            Badge(
                id="better-together", name="Better Together", icon="👥",
                description="Collaborate in a workspace with someone else",
                earned=collaborative,
            ),
            Badge(
                id="completionist", name="Completionist", icon="🏆",
                description="Solve every problem in the catalog",
                earned=bool(problems) and len(solved_ids) == len(problems),
            ),
            Badge(
                id="clock-beater", name="Clock Beater", icon="⏱️",
                description="Finish a mock interview with every part accepted, before time",
                earned=clock_beater,
            ),
            Badge(
                id="pacer", name="Pacer", icon="🏃",
                description="Reach every part of a mock interview within 110% of its budget",
                earned=pacer,
            ),
        ]

    async def _interview_badges(self, user: User, subs: list[Submission]) -> tuple[bool, bool]:
        """Clock Beater: a `finished` session where every stage has an accept.
        Pacer: a completed session (finished/expired) that reached every
        stage, each within 110% of its budget."""
        if self._sessions is None or self._stages is None:
            return False, False
        from app.services.interview_service import scaled_budgets, session_end, stage_times

        clock_beater = pacer = False
        by_session: dict[str, list[Submission]] = defaultdict(list)
        for s in subs:
            if s.interview_session_id:
                by_session[s.interview_session_id].append(s)
        now = datetime.now(UTC)
        for session in await self._sessions.list_by_user(user.id):
            if session.status not in ("finished", "expired"):
                continue
            template = (
                await self._templates.get_by_id(session.template_id) if self._templates else None
            )
            stages = await self._stages.list_by_template(session.template_id)
            if not stages or template is None:
                continue
            budgets = scaled_budgets(template, stages, session)
            accepted_problems = {
                s.problem_id for s in by_session.get(session.id, []) if s.verdict == "accepted"
            }
            if session.status == "finished" and all(
                st.problem_id in accepted_problems for st in stages
            ):
                clock_beater = True
            if session.unlocked_through >= len(stages) and all(budgets.values()):
                spent = stage_times(session.timeline, session_end(session, now))
                if all(
                    spent.get(st.ordinal, 0.0) <= 1.1 * (budgets[st.ordinal] or 0) for st in stages
                ):
                    pacer = True
        return clock_beater, pacer


def _hour_utc(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).hour
