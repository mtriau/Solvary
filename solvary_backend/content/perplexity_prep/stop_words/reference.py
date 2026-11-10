"""Ideal solution: Stop Words, all three parts.

Part 1: text_before_stop(text, stop_words): earliest substring match wins.
Part 2: TokenStream(stop_words, window): deque + dict of counts; stop words
        never enter the window; eviction deletes zero counts; top_k sorts by
        (-count, token).
Part 3: StopStream(stop_words).feed(chunk): buffer the not-yet-emitted
        text; if a stop word completes, emit everything before its earliest
        occurrence and go silent forever; otherwise withhold the longest
        suffix of the buffer that is a proper prefix of some stop word and
        emit the rest.

Shape an interviewer expects:
  - Part 1 is min over text.find; empty-string stop words are skipped.
  - Part 2 keeps counts in step with the deque; the "no zero entries"
    sentence is the delete-on-zero branch. Counter.most_common is NOT used
    for top_k because its tie order is insertion order, not alphabetical.
  - Part 3 holdback: "I can only emit what can no longer be the start of a
    stop word." Everything emitted is dropped from the buffer, so memory is
    O(max stop word length). A fixed holdback of max_len - 1 is the simpler
    baseline; the precise rule (longest suffix that is a proper prefix) is
    what the provided tests pin, because it emits as early as possible.
"""

from collections import deque


# ---------------------------------------------------------------- Part 1

def _first_stop_position(text: str, stop_words: list[str]) -> int | None:
    """Index of the earliest occurrence of any non-empty stop word, else None."""
    best: int | None = None
    for word in stop_words:
        if not word:
            continue
        pos = text.find(word)
        if pos != -1 and (best is None or pos < best):
            best = pos
    return best


def text_before_stop(text: str, stop_words: list[str]) -> str:
    """O(len(text) * number of stop words)."""
    pos = _first_stop_position(text, stop_words)
    return text if pos is None else text[:pos]


# ---------------------------------------------------------------- Part 2

class TokenStream:
    def __init__(self, stop_words: set[str], window: int) -> None:
        self._stop = set(stop_words)
        self._window = window
        self._recent: deque[str] = deque()
        self._counts: dict[str, int] = {}

    def push(self, token: str) -> None:
        """O(1). A stop word is dropped before it can touch the window."""
        if token in self._stop:
            return
        self._recent.append(token)
        self._counts[token] = self._counts.get(token, 0) + 1
        if len(self._recent) > self._window:
            old = self._recent.popleft()
            self._counts[old] -= 1
            if self._counts[old] == 0:
                del self._counts[old]

    def counts(self) -> dict[str, int]:
        return dict(self._counts)

    def top_k(self, k: int) -> list[str]:
        """O(d log d) over d distinct tokens; count desc, then alphabetical."""
        if k <= 0:
            return []
        return sorted(self._counts, key=lambda t: (-self._counts[t], t))[:k]


# ---------------------------------------------------------------- Part 3

class StopStream:
    def __init__(self, stop_words: list[str]) -> None:
        self._stop = [w for w in stop_words if w]
        self._max_hold = max((len(w) for w in self._stop), default=1) - 1
        self._pending = ""      # buffered text not yet emitted
        self._done = False

    def feed(self, chunk: str) -> str:
        if self._done:
            return ""
        self._pending += chunk
        pos = _first_stop_position(self._pending, self._stop)
        if pos is not None:
            self._done = True
            out, self._pending = self._pending[:pos], ""
            return out
        hold = self._possible_prefix_length()
        cut = len(self._pending) - hold
        out, self._pending = self._pending[:cut], self._pending[cut:]
        return out

    def _possible_prefix_length(self) -> int:
        """Length of the longest suffix of the buffer that is a proper prefix
        of some stop word. Bounded by max stop word length - 1."""
        text = self._pending
        for n in range(min(self._max_hold, len(text)), 0, -1):
            tail = text[-n:]
            if any(len(w) > n and w.startswith(tail) for w in self._stop):
                return n
        return 0


if __name__ == "__main__":
    assert text_before_stop("the quick brown fox jumps", ["fox", "jumps"]) == "the quick brown "
    assert text_before_stop("hello world", ["xyz"]) == "hello world"
    assert text_before_stop("stop now", ["stop"]) == ""
    assert text_before_stop("a cat sat", ["sat", "cat"]) == "a "
    assert text_before_stop("bananas", ["nan", "ana"]) == "b"
    assert text_before_stop("", ["a"]) == ""
    assert text_before_stop("abc", []) == "abc"
    assert text_before_stop("abc", ["", "c"]) == "ab"

    ts = TokenStream({"the"}, 3)
    for t in ("a", "b", "a", "c"):
        ts.push(t)
    assert ts.counts() == {"b": 1, "a": 1, "c": 1}
    ts.push("a")
    assert ts.counts() == {"a": 2, "c": 1}
    ts.push("the")
    assert ts.counts() == {"a": 2, "c": 1}
    assert ts.top_k(5) == ["a", "c"]

    ss = StopStream(["fox"])
    assert ss.feed("the quick brown fo") == "the quick brown "
    assert ss.feed("x jumps") == ""
    assert ss.feed("more") == ""
    ss = StopStream(["fox"])
    assert ss.feed("abc") == "abc"
    assert ss.feed("fo") == ""
    assert ss.feed("g") == "fog"
    print("OK")
