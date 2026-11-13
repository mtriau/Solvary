"""
Seed the AI-company practice set as mock interviews.

Usage:
    python -m scripts.seed_ai_prep            # create templates that don't exist yet
    python -m scripts.seed_ai_prep --refresh  # re-read content/ai_prep and update in place

Source: content/ai_prep/ — multi-part problems reconstructed from candidate
reports (Nov 2025 – Nov 2026) at Anthropic, OpenAI, Coinbase, Meta, Airbnb,
Decagon, Snowflake and xAI; see reports/AI company coding interview problems.md
at the monorepo root for the sources and confidence per problem. Two shapes:

- CodeSignal Industry Coding Assessment (ICA) style: 90 minutes, four levels
  that extend the same class, the next level unlocking when the suite is green.
- Live design-and-extend screens: 45–60 minutes, three to five parts added by
  the interviewer.

Every problem is judged in `pytest` mode and reuses the Perplexity seeder's
builders (scripts/seed_perplexity.py). Templates are idempotent (existing
slugs are skipped); `--refresh` updates statements, editorials, stubs and, when
the test ids are unchanged, the harness.
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

CONTENT = Path(__file__).resolve().parent.parent / "content" / "ai_prep"

ICA_RULES = (
    "CodeSignal-style **Industry Coding Assessment**, reconstructed from 2026 candidate"
    " reports: **90 minutes, one class, four levels** that extend the same code; the next"
    " level unlocks when the suite is green (real assessments show each level's tests and"
    " score partial credit, 200–600). Levels 1–2 are short; level 3 is where time enters"
    " (timestamps, TTL, scheduled work processed lazily) and where most candidates stall;"
    " level 4 rewrites state (restore, merge) and must respect everything before it. Three"
    " clean levels beat four broken ones. Stdlib only, no AI."
)

SCREEN_RULES = (
    "Live **design-and-extend** coding screen, reconstructed from 2026 candidate reports:"
    " one problem whose requirements arrive in parts on the same code; the interviewer"
    " adds the next part when the current one works. Each part ships with a **provided"
    " pytest suite** (under *Provided tests*; run it with **Submit**). Graded on working"
    " code first, then a data model that absorbs the next part without a rewrite, your"
    " own edge-case tests, and narrated trade-offs. Finishing the last part is not"
    " required; running out of time on the second-to-last one usually is a rejection."
)

SPECS: list[tuple[Spec, str]] = [
    (
        Spec(
            "memory_db",
            "In-Memory Database",
            "medium",
            ["design", "hashmap", "ttl"],
            90,
            [
                ("SET, GET, DELETE", 12),
                ("SCAN and SCAN_BY_PREFIX", 18),
                ("Timestamps and TTL", 30),
                ("BACKUP and RESTORE", 30),
            ],
            "Dict of dicts; a (value, expires_at) per field; backups as snapshots keyed by"
            " time with TTLs recomputed on restore",
        ),
        ICA_RULES + " Reported at Anthropic (the most common OA), OpenAI and Coinbase.",
    ),
    (
        Spec(
            "bank_system",
            "Banking System",
            "medium",
            ["design", "simulation", "bisect"],
            90,
            [
                ("Accounts, deposits, transfers", 10),
                ("Top spenders", 15),
                ("Scheduled payments", 35),
                ("Merge accounts", 30),
            ],
            "Process due scheduled payments at the top of every operation; per-account"
            " (timestamp, balance) checkpoints + bisect for historical balance",
        ),
        ICA_RULES + " Reported at Coinbase, Meta, Airbnb and Circle; Anthropic uses a variant.",
    ),
    (
        Spec(
            "grid_infection",
            "Grid Infection",
            "medium",
            ["grid", "bfs", "simulation"],
            60,
            [
                ("Simultaneous spread, days to stabilise", 12),
                ("Immune cells", 8),
                ("Recovery", 12),
                ("Expiring immunity", 14),
                ("Burn intervention", 14),
            ],
            "One simulate_days core with per-cell timers; simultaneous updates from a frozen"
            " copy; cycle detection on the full state; brute-force the burn choice",
        ),
        SCREEN_RULES
        + " This is OpenAI's signature five-part problem (60 min); finishing the first three"
        " cleanly is the usual bar.",
    ),
    (
        Spec(
            "recipe_cart",
            "Recipe Shopping Cart",
            "medium",
            ["design", "stack", "versioning"],
            45,
            [
                ("Recipes and bulk discounts", 15),
                ("Versions and checkout", 15),
                ("Nested transactions", 15),
            ],
            "Ingredient counts + an operations log (not snapshots) replayed for checkout;"
            " a stack of undo logs for nested begin/commit/abort",
        ),
        SCREEN_RULES
        + " Decagon's most-reported phone-screen problem (45 min, usually followed by a short"
        " counting problem); the interviewer insisted on space-efficient history.",
    ),
    (
        Spec(
            "rate_limiter",
            "Tiered Rate Limiter",
            "medium",
            ["design", "token-bucket"],
            60,
            [
                ("Tiers and a default policy", 15),
                ("Runtime updates", 10),
                ("Injectable clock and observability", 15),
                ("Compound rules and a shared store", 20),
            ],
            "Token bucket per (client, scope) in one store; refill = elapsed x rate capped at"
            " capacity; all-or-nothing consumption across buckets",
        ),
        SCREEN_RULES
        + " Snowflake's 60-min phone screen (first-hand Aug 2026: rejected for running out of"
        " time before the last follow-up); xAI escalates the same way.",
    ),
]


def _title(spec: Spec) -> str:
    return f"{spec.title} ({len(spec.parts)} parts, {spec.duration_min} min)"


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

        for spec, rules in SPECS:
            slug = f"ai-{spec.slug}"
            if await tpl_repo.get_by_slug(slug):
                print(f"template {slug}: exists")
                continue
            if not (CONTENT / spec.folder).is_dir():
                print(f"template {slug}: content folder missing, skipped")
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
                title=_title(spec),
                description_md=(
                    f"{rules}\n\nOne shared file `{spec.module}.py`; Part N's suite includes"
                    f" parts 1..N-1. The next part unlocks when the suite is green."
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
    """Re-read content/ai_prep and update already-seeded problems in place
    (statement, editorial, starter code; harness only when the test ids are
    unchanged). Test cases and sessions are never rewritten."""
    if not CONTENT.is_dir():
        raise SystemExit(f"content folder missing: {CONTENT}")
    async with async_session_factory() as session:
        prob_repo = SQLAlchemyProblemRepository(session)
        tc_repo = SQLAlchemyTestCaseRepository(session)
        tpl_repo = SQLAlchemyInterviewTemplateRepository(session)
        stage_repo = SQLAlchemyInterviewStageRepository(session)

        for spec, _ in SPECS:
            slug = f"ai-{spec.slug}"
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
