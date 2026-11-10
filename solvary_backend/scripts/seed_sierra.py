"""
Seed the Sierra coding-screen practice set as mock interviews.

Usage:
    python -m scripts.seed_sierra

Source: content/sierra_prep/ (statements, stubs, provided pytest suites and
reference solutions), reconstructed from candidate reports of Sierra's
software-engineering phone screens (Nov 2025 – Oct 2026; see
reports/Sierra coding interview problems.md at the monorepo root). Every
problem is judged in `pytest` mode and reuses the Perplexity seeder's
builders (scripts/seed_perplexity.py).

Templates (idempotent — slugs that exist are skipped): one `levels`
interview per problem, three parts each, 25–30 minutes, the next part
unlocking when the suite is green.
"""

import asyncio
from pathlib import Path

from sqlalchemy import select

import app.db.tables  # noqa: F401 — register tables with Base.metadata
from app.db.engine import async_session_factory
from app.db.tables import UserRow
from app.repositories.sqlalchemy_interview_repository import (
    SQLAlchemyInterviewStageRepository,
    SQLAlchemyInterviewTemplateRepository,
)
from app.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
from app.repositories.sqlalchemy_testcase_repository import SQLAlchemyTestCaseRepository
from scripts.seed_interviews import _ensure_problem
from scripts.seed_perplexity import Spec, _create_template, build_parts

CONTENT = Path(__file__).resolve().parent.parent / "content" / "sierra_prep"

GROUND_RULES = (
    "Sierra-style phone screen, reconstructed from candidate reports (Nov 2025 – Oct"
    " 2026): CoderPad, **no AI tools**, Python, about **30 minutes of coding for three"
    " parts**, each adding requirements on top of your existing code. Finishing two of"
    " three parts has been enough to advance; the third is usually narrated, not"
    " finished. Each part ships with a **provided pytest suite** — read it under"
    " *Provided tests*, run it with **Submit**. Graded on working code first, then"
    " extensible structure and clear tradeoff reasoning. Candidates report the time sink"
    " is I/O plumbing and types, not algorithms."
)

SPECS: list[Spec] = [
    Spec(
        "conversation_history",
        "Conversation History: paginate, then compact",
        "medium",
        ["api", "pagination", "deque"],
        30,
        [
            ("Paginated fetch with retries", 10),
            ("Compact to a token budget", 10),
            ("Incremental history with tool units", 10),
        ],
        "Cursor loop with per-cursor retry; deque + running total, pinned list merged by seq",
    ),
    Spec(
        "product_feed",
        "Product Feed: flaky API, fallbacks, merge",
        "medium",
        ["api", "graph", "dedupe"],
        30,
        [
            ("Fetch all pages with retries", 8),
            ("Resolve fallback IDs", 12),
            ("Merge listings by SKU", 10),
        ],
        "Retry loop; iterative DFS with a seen-set; dict grouping with fresh objects",
    ),
    Spec(
        "markdown_chunker",
        "Markdown Chunker",
        "medium",
        ["string", "parsing"],
        30,
        [("Greedy line packing", 8), ("Repeat active headers", 14), ("Atomic code fences", 8)],
        "Header stack + greedy packing over units (a fence is one unit)",
    ),
    Spec(
        "debug_view",
        "Debug View: log intervals",
        "easy",
        ["intervals", "sorting", "sweep"],
        25,
        [
            ("Merge overlapping segments", 10),
            ("Overlap and gap flags", 7),
            ("Gaps and max concurrency", 8),
        ],
        "Sort once, sweep with furthest-end tracking; end-before-start at equal times",
    ),
    Spec(
        "keyboard",
        "Keyboard with Undo/Redo",
        "medium",
        ["design", "stack"],
        30,
        [("type / backspace", 6), ("undo / redo", 10), ("Cursor-aware editing", 14)],
        "Snapshot stacks of (before, after) states; moves don't touch the stacks",
    ),
    Spec(
        "spreadsheet",
        "Spreadsheet: circular references",
        "medium",
        ["graph", "dfs", "topological-sort"],
        30,
        [
            ("Cells and formulas", 10),
            ("Reject cycles", 10),
            ("Deep sheets, dependents, evaluation order", 10),
        ],
        "Reference graph; iterative DFS with per-call memo; reverse graph by scan",
    ),
    Spec(
        "merch_catalog",
        "Retry + Merchandise Catalog",
        "easy",
        ["retry", "graph", "bfs"],
        25,
        [
            ("Exponential retry with timeout", 10),
            ("Related-items tree", 8),
            ("Cycle-safe, bounded traversal", 7),
        ],
        "Backoff loop with injected clock; path-set DFS for the tree, BFS for reachability",
    ),
]


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

        for spec in SPECS:
            slug = f"sierra-{spec.slug}"
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
                title=f"Sierra: {spec.title} ({len(spec.parts)} parts, {spec.duration_min} min)",
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

        await session.commit()


async def refresh() -> None:
    """Re-read content/sierra_prep and update already-seeded problems in place:
    statement, editorial, starter code and, when the provided test ids are
    unchanged, the harness. Test cases are never rewritten; a part whose test
    ids changed keeps its old harness and is reported."""
    if not CONTENT.is_dir():
        raise SystemExit(f"content folder missing: {CONTENT}")
    async with async_session_factory() as session:
        prob_repo = SQLAlchemyProblemRepository(session)
        tc_repo = SQLAlchemyTestCaseRepository(session)
        tpl_repo = SQLAlchemyInterviewTemplateRepository(session)
        stage_repo = SQLAlchemyInterviewStageRepository(session)

        for spec in SPECS:
            slug = f"sierra-{spec.slug}"
            template = await tpl_repo.get_by_slug(slug)
            if template is None:
                print(f"template {slug}: not seeded yet (run without --refresh)")
                continue
            stages = await stage_repo.list_by_template(template.id)
            parts = build_parts(spec, CONTENT / spec.folder, is_public=False)
            if len(stages) != len(parts):
                print(f"template {slug}: {len(stages)} stages vs {len(parts)} parts, skipped")
                continue
            print(f"template {slug}:")
            for stage, built in zip(stages, parts):
                problem = await prob_repo.get_by_id(stage.problem_id)
                if problem is None:
                    print(f"  stage {stage.ordinal}: problem {stage.problem_id} missing")
                    continue
                problem.statement_md = built.problem.statement_md
                problem.editorial_md = built.problem.editorial_md
                problem.starter_code = built.problem.starter_code
                old_ids = sorted(tc.stdin for tc in await tc_repo.list_by_problem(problem.id))
                new_ids = sorted(c.stdin for c in built.cases)
                note = ""
                if old_ids == new_ids:
                    problem.harness = built.problem.harness
                else:
                    note = " (test ids differ: harness kept, re-seed to replace)"
                await prob_repo.update(problem)
                print(f"  {problem.slug}: statement + editorial refreshed{note}")

        await session.commit()


if __name__ == "__main__":
    import sys

    asyncio.run(refresh() if "--refresh" in sys.argv[1:] else seed())
