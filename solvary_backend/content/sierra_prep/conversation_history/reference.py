from collections import deque
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


# ── Part 1 ─────────────────────────────────────────────────────────────


def fetch_all(fetch_page, *, max_retries: int = 3) -> list[Message]:
    out: list[Message] = []
    seen: set = set()
    cursor = None
    while True:
        if cursor in seen:
            raise PaginationError(f"cursor repeated: {cursor!r}")
        seen.add(cursor)
        attempt = 0
        while True:
            try:
                page, nxt = fetch_page(cursor)
                break
            except TransientError:
                attempt += 1
                if attempt > max_retries:
                    raise
        out.extend(page)
        if nxt is None:
            return out
        cursor = nxt


# ── Part 2 ─────────────────────────────────────────────────────────────


def compact(messages: list[Message], limit: int) -> list[Message]:
    total = sum(m.tokens for m in messages)
    if total <= limit:
        return list(messages)
    kept = list(messages)
    i = 0
    while total > limit and i < len(kept) - 1:
        m = kept[i]
        if m.role == "system":
            i += 1
            continue
        del kept[i]
        total -= m.tokens
    return kept


# ── Part 3 ─────────────────────────────────────────────────────────────


class History:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._pinned: list[tuple[int, Message]] = []
        self._window: deque[tuple[int, Message]] = deque()
        self._total = 0
        self._seq = 0

    def append(self, message: Message) -> None:
        self._seq += 1
        entry = (self._seq, message)
        if message.role == "system":
            self._pinned.append(entry)
        else:
            self._window.append(entry)
        self._total += message.tokens
        self._trim()

    def _trim(self) -> None:
        while self._total > self.limit and len(self._window) > 1:
            _, oldest = self._window[0]
            unit_len = 1
            if oldest.role == "assistant" and oldest.call_id is not None:
                while (
                    unit_len < len(self._window)
                    and self._window[unit_len][1].role == "tool"
                    and self._window[unit_len][1].call_id == oldest.call_id
                ):
                    unit_len += 1
            if unit_len >= len(self._window):
                return  # the unit contains the most recent message: keep it
            for _ in range(unit_len):
                _, m = self._window.popleft()
                self._total -= m.tokens

    def messages(self) -> list[Message]:
        merged = sorted(self._pinned + list(self._window), key=lambda e: e[0])
        return [m for _, m in merged]

    def total_tokens(self) -> int:
        return self._total
