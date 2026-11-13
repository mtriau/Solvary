"""
Interviewer agent (SOLVARY_INTERVIEWER_DESIGN.md §6).

One row per message in the interviewer transcript of a mock-interview
session. The rows double as the model's conversation history: a `user`
turn stores what the candidate said (or the event lines that triggered
the turn) plus a one-line digest of the screen at the time; an `assistant`
turn stores the reply, `[silent]`, or `[refused]`.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

TurnRole = Literal["user", "assistant"]
TurnTrigger = Literal["speech", "typed", "event", "opening"]

SILENT = "[silent]"
REFUSED = "[refused]"


@dataclass
class InterviewerTurn:
    id: str
    session_id: str
    user_id: str
    ordinal: int  # 1-based within the session
    role: TurnRole
    content: str
    trigger: TurnTrigger | None = None  # user turns only
    # user turns only: "stage 2 · 14:05 left · judge wrong_answer 5/7 · code 41 lines"
    digest: str = ""
    silent: bool = False  # assistant turns: the model chose not to speak
    model: str | None = None  # assistant turns
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
