from dataclasses import dataclass, field
from typing import Literal

Checker = Literal["exact", "float_tolerance", "unordered_lines"]


@dataclass
class TestCase:
    id: str
    problem_id: str
    ordinal: int
    stdin: str
    expected_stdout: str
    checker: Checker = "exact"
    checker_args: dict = field(default_factory=dict)  # e.g. {"epsilon": 1e-6}
    is_sample: bool = False  # sample = visible to user
    weight: int = 1
    time_limit_s: float | None = None
    memory_kb: int | None = None
