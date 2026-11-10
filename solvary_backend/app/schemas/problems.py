from typing import Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]
Checker = Literal["exact", "float_tolerance", "unordered_lines"]
JudgeMode = Literal["stdio", "signature", "pytest"]


# ── Test cases ─────────────────────────────────────────────────────


class TestCaseSample(BaseModel):
    """Sample test case — the only shape ever exposed to non-admins."""

    ordinal: int
    stdin: str
    expected_stdout: str


class TestCaseAdmin(BaseModel):
    """Full test case — admin authoring view (includes hidden cases)."""

    id: str
    ordinal: int
    stdin: str
    expected_stdout: str
    checker: Checker
    checker_args: dict
    is_sample: bool
    weight: int
    time_limit_s: float | None
    memory_kb: int | None


class TestCaseCreate(BaseModel):
    ordinal: int
    stdin: str
    expected_stdout: str
    checker: Checker = "exact"
    checker_args: dict = Field(default_factory=dict)
    is_sample: bool = False
    weight: int = 1
    time_limit_s: float | None = None
    memory_kb: int | None = None


# ── Problems ───────────────────────────────────────────────────────


class ProblemSummary(BaseModel):
    id: str
    slug: str
    title: str
    difficulty: Difficulty
    tags: list[str]


class ProblemDetail(ProblemSummary):
    statement_md: str
    starter_code: dict[str, str]
    judge_mode: JudgeMode
    time_limit_s: float
    memory_kb: int
    sample_testcases: list[TestCaseSample]
    # pytest mode: the provided suite files the candidate may read
    harness_files: dict[str, str] | None = None


class ProblemCreate(BaseModel):
    slug: str
    title: str
    difficulty: Difficulty
    statement_md: str
    tags: list[str] = Field(default_factory=list)
    starter_code: dict[str, str] = Field(default_factory=dict)
    function_signature: str | None = None
    judge_mode: JudgeMode = "stdio"
    harness: dict | None = None
    time_limit_s: float = 5.0
    memory_kb: int = 256_000
    editorial_md: str | None = None
    is_public: bool = True


class ProblemUpdate(BaseModel):
    title: str | None = None
    difficulty: Difficulty | None = None
    statement_md: str | None = None
    tags: list[str] | None = None
    starter_code: dict[str, str] | None = None
    function_signature: str | None = None
    time_limit_s: float | None = None
    memory_kb: int | None = None
    editorial_md: str | None = None
    is_public: bool | None = None
