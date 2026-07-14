"""
Seed the problem catalog (idempotent — skips slugs that already exist).

Usage:
    python -m scripts.seed_problems

Requires an admin user (run scripts.seed_admin first) — problems are
attributed to the first admin found.
"""

import asyncio
import uuid

from sqlalchemy import select

import app.db.tables  # noqa: F401 — register tables with Base.metadata
from app.db.base import Base
from app.db.engine import async_session_factory, engine
from app.db.tables import UserRow
from app.models.problem import Problem
from app.models.testcase import TestCase
from app.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
from app.repositories.sqlalchemy_testcase_repository import SQLAlchemyTestCaseRepository

PROBLEMS: list[tuple[Problem, list[TestCase]]] = []


def _problem(  # helper keeps the catalog below readable
    slug: str,
    title: str,
    difficulty: str,
    statement_md: str,
    tags: list[str],
    starter_python: str,
    starter_javascript: str,
    cases: list[dict],
) -> None:
    prob_id = f"prob_{uuid.uuid4().hex[:8]}"
    problem = Problem(
        id=prob_id,
        slug=slug,
        title=title,
        difficulty=difficulty,  # type: ignore[arg-type]
        statement_md=statement_md,
        tags=tags,
        starter_code={"python": starter_python, "javascript": starter_javascript},
        created_by="",  # filled at seed time
    )
    testcases = [
        TestCase(
            id=f"tc_{uuid.uuid4().hex[:8]}",
            problem_id=prob_id,
            ordinal=i + 1,
            stdin=c["stdin"],
            expected_stdout=c["expected_stdout"],
            checker=c.get("checker", "exact"),
            checker_args=c.get("checker_args", {}),
            is_sample=c.get("is_sample", False),
        )
        for i, c in enumerate(cases)
    ]
    PROBLEMS.append((problem, testcases))


# ── Catalog ────────────────────────────────────────────────────────

_problem(
    slug="two-sum",
    title="Two Sum",
    difficulty="easy",
    statement_md=(
        "Given a list of integers and a target, print the **indices** of the two"
        " numbers that add up to the target.\n\n"
        "### Input\nFirst line: `n target`.\nSecond line: `n` space-separated integers.\n\n"
        "### Output\nThe two indices (ascending), space-separated.\n\n"
        "### Example\n```\nInput:\n4 9\n2 7 11 15\n\nOutput:\n0 1\n```\n"
    ),
    tags=["array", "hash-map"],
    starter_python=(
        "import sys\n\n"
        "def solve():\n"
        "    data = sys.stdin.read().split()\n"
        "    # n, target = int(data[0]), int(data[1]); nums = data[2:]\n"
        "    pass\n\n"
        "solve()\n"
    ),
    starter_javascript=(
        "const data = require('fs').readFileSync(0, 'utf8').split(/\\s+/);\n"
        "// const [n, target, ...nums] = data.map(Number);\n"
    ),
    cases=[
        {"stdin": "4 9\n2 7 11 15\n", "expected_stdout": "0 1\n", "is_sample": True},
        {"stdin": "3 6\n3 2 4\n", "expected_stdout": "1 2\n", "is_sample": True},
        {"stdin": "2 6\n3 3\n", "expected_stdout": "0 1\n"},
        {"stdin": "5 0\n-3 4 3 90 1\n", "expected_stdout": "0 2\n"},
    ],
)

_problem(
    slug="fizzbuzz",
    title="FizzBuzz",
    difficulty="easy",
    statement_md=(
        "Print the numbers from 1 to `n`, but for multiples of 3 print `Fizz`,"
        " for multiples of 5 print `Buzz`, and for multiples of both print `FizzBuzz`.\n\n"
        "### Input\nA single integer `n`.\n\n"
        "### Output\n`n` lines.\n"
    ),
    tags=["math", "implementation"],
    starter_python="n = int(input())\n# print each line\n",
    starter_javascript=(
        "const n = Number(require('fs').readFileSync(0, 'utf8').trim());\n"
    ),
    cases=[
        {"stdin": "5\n", "expected_stdout": "1\n2\nFizz\n4\nBuzz\n", "is_sample": True},
        {
            "stdin": "15\n",
            "expected_stdout": (
                "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n"
            ),
        },
        {"stdin": "1\n", "expected_stdout": "1\n"},
    ],
)

_problem(
    slug="mean-of-list",
    title="Mean of a List",
    difficulty="easy",
    statement_md=(
        "Print the arithmetic mean of a list of numbers, to any reasonable precision"
        " (answers within `1e-6` are accepted).\n\n"
        "### Input\nFirst line: `n`.\nSecond line: `n` space-separated numbers.\n\n"
        "### Output\nThe mean.\n"
    ),
    tags=["math"],
    starter_python=(
        "import sys\n\n"
        "data = sys.stdin.read().split()\n"
        "# n = int(data[0]); nums = list(map(float, data[1:]))\n"
    ),
    starter_javascript=(
        "const data = require('fs').readFileSync(0, 'utf8')\n"
        "  .split(/\\s+/).filter(Boolean).map(Number);\n"
    ),
    cases=[
        {
            "stdin": "4\n1 2 3 4\n",
            "expected_stdout": "2.5\n",
            "is_sample": True,
            "checker": "float_tolerance",
            "checker_args": {"epsilon": 1e-6},
        },
        {
            "stdin": "3\n0.1 0.2 0.3\n",
            "expected_stdout": "0.2\n",
            "checker": "float_tolerance",
            "checker_args": {"epsilon": 1e-6},
        },
    ],
)


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        result = await session.execute(
            select(UserRow).where(UserRow.role == "admin").limit(1)
        )
        admin = result.scalar_one_or_none()
        if admin is None:
            raise SystemExit("No admin user found — run `python -m scripts.seed_admin` first")

        problem_repo = SQLAlchemyProblemRepository(session)
        testcase_repo = SQLAlchemyTestCaseRepository(session)

        created = skipped = 0
        for problem, cases in PROBLEMS:
            if await problem_repo.get_by_slug(problem.slug):
                skipped += 1
                continue
            problem.created_by = admin.id
            await problem_repo.create(problem)
            for case in cases:
                await testcase_repo.create(case)
            created += 1
            print(f"Seeded {problem.slug} ({len(cases)} cases)")

        await session.commit()
        print(f"Done: {created} created, {skipped} already existed")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
