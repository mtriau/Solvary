from dataclasses import dataclass


class TransientError(Exception):
    """`fetch_page` may raise this; the same cursor can be retried."""


class PaginationError(Exception):
    """The API misbehaved (a cursor came back a second time)."""


@dataclass(frozen=True)
class Message:
    id: str
    role: str  # "system" | "user" | "assistant" | "tool"
    text: str
    tokens: int
    call_id: str | None = None  # Part 3: links a tool call to its result


def fetch_all(fetch_page, *, max_retries: int = 3) -> list[Message]:
    """Part 1: pull every page of the conversation. See the statement."""
    raise NotImplementedError
