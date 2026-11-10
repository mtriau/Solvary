"""
Seed the Perplexity coding-screen practice set as mock interviews.

Usage:
    python -m scripts.seed_perplexity

Source: content/perplexity_prep/ (statements, stubs, provided pytest suites
and reference solutions). Every problem is judged in `pytest` mode: the
candidate implements a module, Submit runs the provided suite inside the
sandbox, and each test reports by name (SOLVARY_INTERVIEWS_DESIGN.md).

Templates (idempotent — slugs that exist are skipped):
  six `levels` interviews, one per multi-part problem (Part N's suite is
  the union of parts 1..N; the next part unlocks when the suite is green)
  one `questions` interview with the four tier-2 single-shot problems
The tier-2 problems are also public, for untimed practice.
"""

import asyncio
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select

import app.db.tables  # noqa: F401 — register tables with Base.metadata
from app.db.engine import async_session_factory
from app.db.tables import UserRow
from app.models.interview import InterviewStage, InterviewTemplate
from app.models.problem import Problem
from app.models.testcase import TestCase
from app.repositories.sqlalchemy_interview_repository import (
    SQLAlchemyInterviewStageRepository,
    SQLAlchemyInterviewTemplateRepository,
)
from app.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
from app.repositories.sqlalchemy_testcase_repository import SQLAlchemyTestCaseRepository
from app.services.execution.pytest_harness import collect_test_ids
from scripts.seed_interviews import _ensure_problem

CONTENT = Path(__file__).resolve().parent.parent / "content" / "perplexity_prep"
RUN_TIME_LIMIT_S = 15.0  # whole suite, one sandbox run (Piston caps at 15 s)

GROUND_RULES = (
    "Perplexity-style live coding screen: the interviewer reveals **Part 1 only**;"
    " later parts come as you finish. Each part ships with a **provided pytest suite**"
    " — read it under *Provided tests*, run it with **Submit**, and debug from the"
    " failures (test names are the hints). Finishing every part is not expected,"
    " but candidates who stopped at Part 2 were rejected. Graded on correctness vs."
    " the requirements first, then methodical debugging, sound abstractions, clean"
    " code, and tradeoff reasoning. \"Don't get sloppy to make progress.\" No thread"
    " safety or wishlist features unless asked."
)


@dataclass
class Spec:
    folder: str
    title: str
    difficulty: str
    tags: list[str]
    duration_min: int
    parts: list[tuple[str, int]]  # (part title, budget minutes)
    pattern: str = ""  # README "core pattern" — editorial only
    module: str = ""
    slug: str = ""

    def __post_init__(self) -> None:
        self.module = self.module or self.folder
        self.slug = self.slug or self.folder.replace("_", "-")


MULTI_PART: list[Spec] = [
    Spec(
        "todo_tracker", "Agent Task Tracker", "medium", ["graph", "bfs", "design"], 60,
        [("CRUD", 12), ("Dependency resolution", 18),
         ("Adding edges later, cycle detection", 18), ("Undo", 12)],
        "Graph with both edge directions, iterative BFS",
    ),
    Spec(
        "unix_filesystem", "In-Memory Unix File System", "medium", ["tree", "design"], 45,
        [("Strict mkdir, touch, write, read, ls", 15), ("rm, rmdir, command runner", 15),
         ("cd, pwd, relative paths", 15)],
        "Tree + one path resolver",
    ),
    Spec(
        "temporal_kv", "Time-Versioned KV Store", "medium", ["binary-search", "design"], 45,
        [("set / get as-of", 12), ("delete + range", 16), ("restore", 17)],
        "Per-key sorted list + bisect, mutation log",
    ),
    Spec(
        "credit_tracker", "Credit Tracker", "hard", ["heap", "simulation"], 50,
        [("add_credit / check_credit", 10), ("subtract_credit", 20),
         ("Out-of-order events", 20)],
        "Sorted events + heap",
    ),
    Spec(
        "stop_words", "Stop Words", "medium", ["string", "sliding-window", "trie"], 40,
        [("Text before the first stop word", 10), ("Token stream with window", 15),
         ("Chunked character stream", 15)],
        "String scan, deque/Counter, trie",
    ),
    Spec(
        "byte_tokenizer", "Byte Tokenizer", "hard", ["string", "simulation"], 45,
        [("tokenize", 15), ("Tokenizer class, detokenize, make it fast", 18),
         ("Count and stream", 12)],
        "Ordered single-pass merges",
    ),
]

TIER2: list[Spec] = [
    Spec("provider_pool", "LLM Provider Pool with Failover", "medium", ["design"], 25,
         [("Provider pool", 25)], module="provider_pool"),
    Spec("beam_search", "Beam Search", "medium", ["heap", "search"], 25,
         [("Beam search", 25)]),
    Spec("citations", "Citation Renumbering", "easy", ["string", "regex"], 20,
         [("Citation renumbering", 20)]),
    Spec("topic_sort", "Topic Sort", "easy", ["sorting"], 20, [("Topic sort", 20)]),
]


# ── statement cleanup ──────────────────────────────────────────────


def split_reveal(text: str) -> tuple[str, str | None]:
    """A PARTn.md → (candidate-facing statement, interviewer notes or None)."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"^(# .*?) \(reveal verbatim\)[ \t]*$", r"\1", text, flags=re.M)
    # interviewer preface between the title and the first rule
    text = re.sub(r"\n\s*Interviewer: .*?\n---\n", "\n", text, count=1, flags=re.S)
    notes = None
    m = re.search(r"\n---\n\s*Interviewer notes[^\n]*\n(.*)$", text, flags=re.S)
    if m:
        notes = m.group(1).strip()
        text = text[: m.start()]
    # pytest invocations → the Submit button
    text = re.sub(
        r"Run the provided tests:\s+`pytest [^`]*`\.\s+Later parts\s+come with\s+their own"
        r" test files\.",
        "Run the provided tests with **Submit**; later parts come with their own test files.",
        text,
    )
    text = re.sub(
        r"Run the provided tests:\s+`pytest [^`]*`\.",
        "Run the provided tests with **Submit**.",
        text,
    )
    text = re.sub(
        r"Provided tests: (`test_[^`]*`) \(copy into `[^`]*`\), then\s+`pytest [^`]*`\.",
        r"Provided tests: \1 (under *Provided tests*); run them with **Submit**.",
        text,
    )
    text = re.sub(
        r"Provided tests: (`test_[^`]*`), then\s+`pytest [^`]*`\.",
        r"Provided tests: \1 (under *Provided tests*); run them with **Submit**.",
        text,
    )
    return text.strip() + "\n", notes


def editorial(reference: str, notes: list[str], pattern: str) -> str:
    out = []
    if pattern:
        out.append(f"**Core pattern:** {pattern}\n")
    if notes:
        out.append("### Interviewer notes\n\n" + "\n\n".join(notes) + "\n")
    out.append("### Reference solution\n\n```python\n" + reference.rstrip() + "\n```\n")
    return "\n".join(out)


# ── building problems ──────────────────────────────────────────────


@dataclass
class Built:
    problem: Problem
    cases: list[TestCase]
    stage_title: str
    budget_s: int
    notes: list[str] = field(default_factory=list)


def build_parts(spec: Spec, folder: Path, is_public: bool) -> list[Built]:
    stub = (folder / f"{spec.module}.py").read_text(encoding="utf-8")
    reference = (folder / "reference.py").read_text(encoding="utf-8")
    built: list[Built] = []
    files: dict[str, str] = {}
    notes_so_far: list[str] = []
    n_parts = len(spec.parts)
    for n, (part_title, budget_min) in enumerate(spec.parts, 1):
        statement, notes = split_reveal((folder / f"PART{n}.md").read_text(encoding="utf-8"))
        if notes:
            notes_so_far.append(f"**Part {n}.** {notes}")
        test_name = f"test_{spec.module}_p{n}.py"
        files[test_name] = (folder / test_name).read_text(encoding="utf-8")
        suite = dict(files)  # cumulative: parts 1..n
        ids = [tid for name, src in suite.items() for tid in collect_test_ids(name, src)]
        assert ids, f"{spec.folder} part {n}: no tests collected"

        pid = f"prob_{uuid.uuid4().hex[:8]}"
        title = spec.title if n_parts == 1 else f"{spec.title} — Part {n}: {part_title}"
        slug = spec.slug if n_parts == 1 else f"{spec.slug}-part-{n}"
        problem = Problem(
            id=pid,
            slug=slug,
            title=title,
            difficulty=spec.difficulty,  # type: ignore[arg-type]
            statement_md=statement,
            tags=["interview", "pytest", *spec.tags],
            starter_code={"python": stub},
            judge_mode="pytest",
            harness={"module": spec.module, "files": suite},
            time_limit_s=RUN_TIME_LIMIT_S,
            editorial_md=editorial(reference, list(notes_so_far), spec.pattern),
            is_public=is_public,
        )
        cases = [
            TestCase(
                id=f"tc_{uuid.uuid4().hex[:8]}",
                problem_id=pid,
                ordinal=i,
                stdin=tid,
                expected_stdout="PASS\n",
                is_sample=True,  # the suite is provided: names and failures are visible
            )
            for i, tid in enumerate(ids, 1)
        ]
        built.append(Built(problem, cases, part_title, budget_min * 60))
    return built


# ── seeding ────────────────────────────────────────────────────────


async def _create_template(
    tpl_repo: SQLAlchemyInterviewTemplateRepository,
    stage_repo: SQLAlchemyInterviewStageRepository,
    *,
    slug: str,
    title: str,
    description_md: str,
    fmt: str,
    duration_min: int,
    advance: str,
    stages: list[tuple[Problem, str, int]],
    admin_id: str,
) -> None:
    template = InterviewTemplate(
        id=f"itpl_{uuid.uuid4().hex[:8]}",
        slug=slug,
        title=title,
        description_md=description_md,
        format=fmt,  # type: ignore[arg-type]
        duration_s=duration_min * 60,
        advance=advance,  # type: ignore[arg-type]
        pacing="coached",
        created_by=admin_id,
    )
    await tpl_repo.create(template)
    for i, (problem, stage_title, budget_s) in enumerate(stages, 1):
        await stage_repo.create(
            InterviewStage(
                id=f"istg_{uuid.uuid4().hex[:8]}",
                template_id=template.id,
                ordinal=i,
                problem_id=problem.id,
                title=stage_title,
                budget_s=budget_s,
            )
        )
    print(f"  created ({len(stages)} stages)")


async def seed() -> None:
    if not CONTENT.is_dir():
        raise SystemExit(f"content folder missing: {CONTENT}")
    async with async_session_factory() as session:
        admin = (
            await session.execute(select(UserRow).where(UserRow.role == "admin").limit(1))
        ).scalar_one_or_none()
        if admin is None:
            raise SystemExit("No admin user — run `python -m scripts.seed_admin` first")

        prob_repo = SQLAlchemyProblemRepository(session)
        tc_repo = SQLAlchemyTestCaseRepository(session)
        tpl_repo = SQLAlchemyInterviewTemplateRepository(session)
        stage_repo = SQLAlchemyInterviewStageRepository(session)

        for spec in MULTI_PART:
            slug = f"perplexity-{spec.slug}"
            if await tpl_repo.get_by_slug(slug):
                print(f"template {slug}: exists")
                continue
            print(f"template {slug}:")
            parts = build_parts(spec, CONTENT / spec.folder, is_public=False)
            stages = []
            for b in parts:
                p = await _ensure_problem(prob_repo, tc_repo, (b.problem, b.cases), admin.id)
                stages.append((p, f"Part {len(stages) + 1}: {b.stage_title}", b.budget_s))
            budgets = " / ".join(str(m) for _, m in spec.parts)
            await _create_template(
                tpl_repo,
                stage_repo,
                slug=slug,
                title=f"{spec.title} ({len(spec.parts)} parts, {spec.duration_min} min)",
                description_md=(
                    f"{GROUND_RULES}\n\nOne shared file `{spec.module}.py`; Part N's suite"
                    f" includes parts 1..N-1. The next part unlocks when the suite is green."
                    f" Suggested pacing: {budgets} minutes."
                ),
                fmt="levels",
                duration_min=spec.duration_min,
                advance="on_accept",
                stages=stages,
                admin_id=admin.id,
            )

        slug = "perplexity-tier-2"
        if await tpl_repo.get_by_slug(slug):
            print(f"template {slug}: exists")
        else:
            print(f"template {slug}:")
            stages = []
            for spec in TIER2:
                (b,) = build_parts(spec, CONTENT / "tier2" / spec.folder, is_public=True)
                p = await _ensure_problem(prob_repo, tc_repo, (b.problem, b.cases), admin.id)
                stages.append((p, spec.title, b.budget_s))
            total = sum(s.duration_min for s in TIER2)
            await _create_template(
                tpl_repo,
                stage_repo,
                slug=slug,
                title=f"Perplexity tier 2: four quick problems ({total} min)",
                description_md=(
                    "Shorter single-shot problems reconstructed from single candidate"
                    " reports (full spec visible, provided pytest suite each). One file per"
                    " problem; switch freely. Suggested pacing: "
                    + " / ".join(str(s.duration_min) for s in TIER2)
                    + " minutes."
                ),
                fmt="questions",
                duration_min=total,
                advance="free",
                stages=stages,
                admin_id=admin.id,
            )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
