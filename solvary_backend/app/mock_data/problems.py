"""Mock problems + test cases for USE_MOCK_DB dev mode (mirrors scripts/seed_problems.py)."""

from app.models.problem import Problem
from app.models.testcase import TestCase

MOCK_PROBLEMS: list[Problem] = [
    Problem(
        id="prob_two_sum",
        slug="two-sum",
        title="Two Sum",
        difficulty="easy",
        statement_md=(
            "Given a list of integers and a target, print the **indices** of the two"
            " numbers that add up to the target.\n\n"
            "**Input:** first line `n target`, second line `n` space-separated integers.\n\n"
            "**Output:** the two indices (ascending), space-separated.\n"
        ),
        tags=["array", "hash-map"],
        starter_code={
            "python": (
                "def solve():\n    # read from stdin, print to stdout\n    pass\n\nsolve()\n"
            ),
            "javascript": (
                "function solve() {\n  // read from stdin, print to stdout\n}\n\nsolve();\n"
            ),
        },
        created_by="user_admin",
    ),
]

MOCK_TESTCASES: list[TestCase] = [
    TestCase(
        id="tc_two_sum_1",
        problem_id="prob_two_sum",
        ordinal=1,
        stdin="4 9\n2 7 11 15\n",
        expected_stdout="0 1\n",
        is_sample=True,
    ),
    TestCase(
        id="tc_two_sum_2",
        problem_id="prob_two_sum",
        ordinal=2,
        stdin="3 6\n3 2 4\n",
        expected_stdout="1 2\n",
        is_sample=False,
    ),
]
