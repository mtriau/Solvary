"""Interviewer agent wire shapes (SOLVARY_INTERVIEWER_DESIGN.md §4.1, §8)."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Trigger = Literal["speech", "typed", "event", "opening"]
MicMode = Literal["open", "push", "off"]
VisiblePane = Literal["judge", "run", "none"]
KeySource = Literal["user", "server", "none"]

MAX_FAILURE_DETAIL = 800
MAX_RUN_OUTPUT = 2000
MAX_EVENT_LINE = 300


# ── client → server: the screen ────────────────────────────────────


class JudgeFailure(BaseModel):
    name: str = Field(max_length=300)  # "test_x_p2.py::test_name" or "Test 3"
    detail: str = Field(default="", max_length=MAX_FAILURE_DETAIL)  # assertion / traceback


class JudgeSnapshot(BaseModel):
    submission_id: str | None = None
    verdict: str = Field(max_length=40)
    passed: int = Field(ge=0)
    total: int = Field(ge=0)
    failures: list[JudgeFailure] = Field(default_factory=list, max_length=12)
    age_s: int = Field(ge=0)  # seconds since the verdict arrived


class RunSnapshot(BaseModel):
    status: str | None = Field(default=None, max_length=40)
    stdin: str = Field(default="", max_length=1000)
    stdout: str = Field(default="", max_length=MAX_RUN_OUTPUT)
    stderr: str = Field(default="", max_length=MAX_RUN_OUTPUT)
    age_s: int = Field(ge=0)


class ScreenContext(BaseModel):
    stage: int = Field(ge=1)  # the part the candidate is looking at
    code: str = ""  # the whole buffer; bounded server-side by execution_max_code_bytes
    code_changed_since_last_turn: bool = True
    judge: JudgeSnapshot | None = None
    run: RunSnapshot | None = None
    visible_pane: VisiblePane = "none"
    seconds_since_last_edit: int = Field(default=0, ge=0)
    mic: MicMode = "off"


class InterviewerTurnRequest(BaseModel):
    trigger: Trigger
    utterance: str | None = Field(default=None, max_length=2000)  # speech / typed
    events: list[str] = Field(default_factory=list, max_length=8)  # §2.3 event lines
    screen: ScreenContext

    @field_validator("events")
    @classmethod
    def _event_lines(cls, v: list[str]) -> list[str]:
        out = []
        for line in v:
            line = " ".join(line.split())
            if line:
                out.append(line[:MAX_EVENT_LINE])
        return out

    @model_validator(mode="after")
    def _needs_words(self) -> "InterviewerTurnRequest":
        if self.trigger in ("speech", "typed"):
            if not self.utterance or not self.utterance.strip():
                raise ValueError("utterance is required for speech and typed turns")
        elif not self.events and self.trigger == "event":
            raise ValueError("an event turn needs at least one event line")
        return self


# ── server → client ────────────────────────────────────────────────


class InterviewerTurnResponse(BaseModel):
    id: str
    ordinal: int
    role: Literal["user", "assistant"]
    trigger: Trigger | None
    content: str
    digest: str
    silent: bool
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    cache_read_input_tokens: int | None
    cache_creation_input_tokens: int | None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=UTC)


class InterviewerTranscript(BaseModel):
    turns: list[InterviewerTurnResponse]
    idle_s: int  # the page fires the idle event after this long (server-configured)
    model: str
    key_source: KeySource
    active: bool  # the session still accepts turns


# ── API key management (/users/me/ai-key) ──────────────────────────


class AiKeyStatus(BaseModel):
    configured: bool
    last4: str | None
    source: KeySource


class AiKeySet(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)

    @field_validator("api_key")
    @classmethod
    def _shape(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("sk-ant-"):
            raise ValueError("Anthropic API keys start with sk-ant-")
        if any(ch.isspace() for ch in v):
            raise ValueError("API key must not contain whitespace")
        return v


class AiKeyTestResult(BaseModel):
    ok: bool
    model: str
    source: KeySource
