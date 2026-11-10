from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]
JudgeMode = Literal["stdio", "signature", "pytest"]

SUPPORTED_LANGUAGES = ("python", "javascript")


@dataclass
class Problem:
    id: str
    slug: str
    title: str
    difficulty: Difficulty
    statement_md: str
    tags: list[str] = field(default_factory=list)
    starter_code: dict[str, str] = field(default_factory=dict)  # language -> code
    function_signature: str | None = None
    judge_mode: JudgeMode = "stdio"
    # pytest mode: {"module": "<import name>", "files": {"test_x_p1.py": src, …}}
    harness: dict | None = None
    time_limit_s: float = 5.0
    memory_kb: int = 256_000
    editorial_md: str | None = None
    is_public: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
