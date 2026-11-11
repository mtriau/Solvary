"""
Drills: very small Python exercises, each practising one idiom.

A drill is an ordinary pytest-mode `Problem` tagged `drill`, `topic:<slug>`
and `order:<nn>`, seeded `is_public=False` so it stays out of the problem
list and the stats pool. This service adds what the drill UI needs on top of
the problem: topic grouping, per-user progress derived from submissions,
and prev/next navigation. Judging is the normal submission pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import NotFoundException
from app.models.problem import Problem
from app.models.user import User
from app.repositories.problem_repository import ProblemRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.schemas.drills import DrillDetail, DrillList, DrillSummary, DrillTopic
from app.schemas.problems import TestCaseSample
from app.services.problem_service import ProblemService

DRILL_TAG = "drill"


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    blurb: str


# Display order and copy for the topics. The seeder validates its content
# folders against this list; an unknown topic is seeded but listed last.
TOPICS: list[Topic] = [
    Topic("comprehensions", "Comprehensions", "Build lists, dicts and sets in one expression."),
    Topic("strings", "Strings", "split, partition, join and f-string format specs."),
    Topic("collections", "Dicts & collections", "Counter, defaultdict, .items(), dict union."),
    Topic("sorting", "Sorting", "key functions, tuple keys, max/min with key."),
    Topic("iteration", "Iteration", "enumerate, zip, next with a default, any/all."),
    Topic("slicing", "Slicing & unpacking", "Star-unpacking, extended slices, % for wrapping."),
    Topic(
        "generators",
        "Generators & itertools",
        "yield, accumulate, groupby, zip on shifted slices.",
    ),
    Topic("patterns", "Pythonic patterns", "EAFP, the walrus, dataclasses, dunder methods."),
    # Interview building blocks: idioms and algorithm skeletons to type without thinking.
    Topic(
        "hashing",
        "Hash-map idioms",
        "seen sets, complement lookups, canonical keys, prefix sums.",
    ),
    Topic(
        "stacks-queues",
        "Stacks & queues",
        "Bracket matching, monotonic stacks, dispatch dicts, deque.",
    ),
    Topic(
        "loops",
        "Loops & exit conditions",
        "divmod loops, iter with a sentinel, bounded retries, binary search.",
    ),
    Topic(
        "pointers",
        "Two pointers & windows",
        "Write indexes, converging pointers, grow-and-shrink windows.",
    ),
    Topic(
        "graphs",
        "Graph skeletons",
        "Adjacency from edges, BFS, iterative DFS, Kahn's algorithm.",
    ),
    Topic(
        "recursion",
        "Recursion & backtracking",
        "Base cases first, functools.cache, choose/explore/un-choose.",
    ),
]
TOPIC_BY_SLUG = {t.slug: t for t in TOPICS}
_TOPIC_RANK = {t.slug: i for i, t in enumerate(TOPICS)}


def topic_of(problem: Problem) -> str:
    for tag in problem.tags:
        if tag.startswith("topic:"):
            return tag.removeprefix("topic:")
    return "misc"


def order_of(problem: Problem) -> int:
    for tag in problem.tags:
        if tag.startswith("order:"):
            try:
                return int(tag.removeprefix("order:"))
            except ValueError:
                break
    return 0


def is_drill(problem: Problem) -> bool:
    return DRILL_TAG in problem.tags


def _sort_key(problem: Problem) -> tuple[int, str, int, str]:
    topic = topic_of(problem)
    return (_TOPIC_RANK.get(topic, len(TOPICS)), topic, order_of(problem), problem.slug)


class DrillService:
    def __init__(
        self,
        problem_repo: ProblemRepository,
        testcase_repo: TestCaseRepository,
        submission_repo: SubmissionRepository,
    ) -> None:
        self._problems = problem_repo
        self._testcases = testcase_repo
        self._submissions = submission_repo

    # ── helpers ────────────────────────────────────────────────────

    async def _all(self) -> list[Problem]:
        drills = [p for p in await self._problems.list_all() if is_drill(p)]
        drills.sort(key=_sort_key)
        return drills

    async def _progress(self, user: User) -> dict[str, tuple[bool, int]]:
        """problem_id -> (solved, attempts) from the user's submissions."""
        solved: set[str] = set()
        attempts: dict[str, int] = {}
        for s in await self._submissions.list_by_user(user.id):
            attempts[s.problem_id] = attempts.get(s.problem_id, 0) + 1
            if s.verdict == "accepted":
                solved.add(s.problem_id)
        return {pid: (pid in solved, n) for pid, n in attempts.items()}

    @staticmethod
    def _summary(p: Problem, progress: dict[str, tuple[bool, int]]) -> DrillSummary:
        solved, attempts = progress.get(p.id, (False, 0))
        return DrillSummary(
            id=p.id,
            slug=p.slug,
            title=p.title,
            topic=topic_of(p),
            order=order_of(p),
            solved=solved,
            attempts=attempts,
        )

    # ── reads ──────────────────────────────────────────────────────

    async def list(self, user: User) -> DrillList:
        drills = await self._all()
        progress = await self._progress(user)
        summaries = [self._summary(p, progress) for p in drills]

        topics: list[DrillTopic] = []
        for summary in summaries:
            if not topics or topics[-1].slug != summary.topic:
                meta = TOPIC_BY_SLUG.get(summary.topic)
                topics.append(
                    DrillTopic(
                        slug=summary.topic,
                        title=meta.title if meta else summary.topic.title(),
                        blurb=meta.blurb if meta else "",
                        drills=[],
                        solved=0,
                        total=0,
                    )
                )
            topics[-1].drills.append(summary)
            topics[-1].total += 1
            topics[-1].solved += int(summary.solved)

        next_slug = next((s.slug for s in summaries if not s.solved), None)
        return DrillList(
            topics=topics,
            solved=sum(t.solved for t in topics),
            total=len(summaries),
            next_slug=next_slug,
        )

    async def get(self, user: User, slug: str) -> DrillDetail:
        drills = await self._all()
        index = next((i for i, p in enumerate(drills) if p.slug == slug), None)
        if index is None:
            raise NotFoundException(f"Drill '{slug}' not found")
        problem = drills[index]
        progress = await self._progress(user)
        solved, attempts = progress.get(problem.id, (False, 0))

        cases = await self._testcases.list_by_problem(problem.id)
        samples = [
            TestCaseSample(ordinal=c.ordinal, stdin=c.stdin, expected_stdout=c.expected_stdout)
            for c in cases
            if c.is_sample
        ]
        base = ProblemService._to_detail(problem, samples)

        topic = topic_of(problem)
        in_topic = [p for p in drills if topic_of(p) == topic]
        meta = TOPIC_BY_SLUG.get(topic)
        after = drills[index + 1 :]
        next_unsolved = next(
            (p.slug for p in after + drills[:index] if not progress.get(p.id, (False, 0))[0]),
            None,
        )
        return DrillDetail(
            **base.model_dump(),
            topic=topic,
            topic_title=meta.title if meta else topic.title(),
            order=order_of(problem),
            position=in_topic.index(problem) + 1,
            topic_total=len(in_topic),
            editorial_md=problem.editorial_md,
            solved=solved,
            attempts=attempts,
            prev_slug=drills[index - 1].slug if index > 0 else None,
            next_slug=after[0].slug if after else None,
            next_unsolved_slug=next_unsolved,
        )
