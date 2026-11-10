"""
Seed the Python idiom drills from content/drills as private pytest-mode problems.

Usage:
    python -m scripts.seed_drills            # create drills that do not exist yet
    python -m scripts.seed_drills --refresh  # also update existing ones in place

Layout: content/drills/<topic>/ORDER lists the drill folders in display
order; each content/drills/<topic>/<slug>/ holds PROBLEM.md (first line is
the `# Title`), <module>.py (stub), reference.py, test_<module>.py and
NOTES.md. Topics are described in app.services.drill_service.TOPICS.

Each drill becomes a `Problem` with judge_mode "pytest", tags
["drill", "topic:<topic>", "order:<nn>", ...], is_public=False, one TestCase
per provided test, and an editorial made of NOTES.md plus the reference.
"""

import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

import app.db.tables  # noqa: F401 — register tables with Base.metadata
from app.db.engine import async_session_factory
from app.db.tables import UserRow
from app.models.problem import Problem
from app.models.testcase import TestCase
from app.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
from app.repositories.sqlalchemy_testcase_repository import SQLAlchemyTestCaseRepository
from app.services.drill_service import DRILL_TAG, TOPIC_BY_SLUG, TOPICS
from app.services.execution.pytest_harness import collect_test_ids
from scripts.seed_perplexity import RUN_TIME_LIMIT_S

CONTENT = Path(__file__).resolve().parent.parent / "content" / "drills"


def iter_content() -> list[tuple[str, int, Path]]:
    """(topic, order, folder) in display order: known topics first, then extras."""
    known = [t.slug for t in TOPICS]
    extra = sorted(p.name for p in CONTENT.iterdir() if p.is_dir() and p.name not in known)
    out: list[tuple[str, int, Path]] = []
    for topic in known + extra:
        order_file = CONTENT / topic / "ORDER"
        if not order_file.is_file():
            continue
        for n, slug in enumerate(order_file.read_text(encoding="utf-8").split(), 1):
            folder = CONTENT / topic / slug
            if not folder.is_dir():
                raise SystemExit(f"{topic}/ORDER lists {slug} but the folder is missing")
            out.append((topic, n, folder))
    return out


def build_drill(topic: str, order: int, folder: Path) -> tuple[Problem, list[TestCase]]:
    slug = folder.name
    module = slug.replace("-", "_")
    read = lambda name: (folder / name).read_text(encoding="utf-8").replace("\r\n", "\n")  # noqa: E731

    statement = read("PROBLEM.md")
    title_line, _, body = statement.partition("\n")
    if not title_line.startswith("# "):
        raise SystemExit(f"{slug}: PROBLEM.md must start with a '# Title' line")
    title = title_line[2:].strip()

    test_name = f"test_{module}.py"
    tests = read(test_name)
    ids = collect_test_ids(test_name, tests)
    if not ids:
        raise SystemExit(f"{slug}: no tests collected from {test_name}")

    editorial = (
        read("NOTES.md").rstrip()
        + "\n\n### Idiomatic solution\n\n```python\n"
        + read("reference.py").rstrip()
        + "\n```\n"
    )

    pid = f"prob_{uuid.uuid4().hex[:8]}"
    problem = Problem(
        id=pid,
        slug=f"drill-{slug}",
        title=title,
        difficulty="easy",
        statement_md=body.strip() + "\n",
        tags=[DRILL_TAG, f"topic:{topic}", f"order:{order:02d}", "pytest", "python"],
        starter_code={"python": read(f"{module}.py")},
        judge_mode="pytest",
        harness={"module": module, "files": {test_name: tests}},
        time_limit_s=RUN_TIME_LIMIT_S,
        editorial_md=editorial,
        is_public=False,
    )
    cases = [
        TestCase(
            id=f"tc_{uuid.uuid4().hex[:8]}",
            problem_id=pid,
            ordinal=i,
            stdin=tid,
            expected_stdout="PASS\n",
            is_sample=True,
        )
        for i, tid in enumerate(ids, 1)
    ]
    return problem, cases


async def seed(refresh: bool = False) -> None:
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

        created = updated = skipped = 0
        for topic, order, folder in iter_content():
            if topic not in TOPIC_BY_SLUG:
                print(f"note: topic '{topic}' is not in drill_service.TOPICS; listed last")
            problem, cases = build_drill(topic, order, folder)
            existing = await prob_repo.get_by_slug(problem.slug)
            if existing is None:
                problem.created_by = admin.id
                await prob_repo.create(problem)
                for c in cases:
                    await tc_repo.create(c)
                print(f"  {problem.slug}: created ({len(cases)} tests)")
                created += 1
            elif refresh:
                existing.title = problem.title
                existing.statement_md = problem.statement_md
                existing.editorial_md = problem.editorial_md
                existing.starter_code = problem.starter_code
                existing.tags = problem.tags
                old_ids = sorted(tc.stdin for tc in await tc_repo.list_by_problem(existing.id))
                new_ids = sorted(c.stdin for c in cases)
                note = ""
                if old_ids == new_ids:
                    existing.harness = problem.harness
                else:
                    note = " (test ids differ: harness kept, delete the problem to re-seed)"
                await prob_repo.update(existing)
                print(f"  {problem.slug}: refreshed{note}")
                updated += 1
            else:
                skipped += 1
        await session.commit()
        print(f"drills: {created} created, {updated} refreshed, {skipped} already present")


if __name__ == "__main__":
    asyncio.run(seed(refresh="--refresh" in sys.argv[1:]))
