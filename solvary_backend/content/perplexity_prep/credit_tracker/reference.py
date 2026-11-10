"""Ideal solution: Credit Tracker, all three parts in ONE class.

Part 1: add_credit / check_credit, grants active on [start, end] inclusive.
Part 2: subtract_credit draws from the grant that expires EARLIEST (ties:
        added first), partial if short; calls arrive in time order.
Part 3: calls arrive in ANY order; check_credit(t) replays events with
        timestamp <= t and returns -1 if any subtraction was ever short.

Shape an interviewer expects:
  - Part 2 is a Ledger with a min-heap keyed (end, insertion_idx). Because
    time only moves forward in Part 2, an expired grant can be dropped for
    good (lazy pop at the top of the heap).
  - Part 3 does NOT rewrite Part 2. It records events and, on each check,
    replays them through a fresh Part 2 Ledger. The replay is a pure
    function of (sorted events, t). O(n log n) per check; state that, and
    name the incremental alternatives (snapshots, cached replay invalidated
    when an older event arrives) as follow-ups rather than building them.

How one class serves all three parts: while calls stay in time order (Parts
1 and 2) a "live" Ledger is kept in step with the recorded events, so
subtract_credit can return the amount it spent in O(log n), exactly as the
Part 2 reveal demands. An out-of-order event (Part 3) invalidates the live
Ledger; from then on subtract_credit for an out-of-order timestamp only
records the event and returns 0 (the Part 3 reveal says the return value is
no longer meaningful; check_credit is the source of truth). Computing an
exact value for an out-of-order subtraction would need a full replay per
call, O(n) each, which is what the scale test rules out.
"""

import heapq
from bisect import bisect_right


# ---------------------------------------------------------------- Part 2 ledger

class _Grant:
    __slots__ = ("start", "end", "remaining")

    def __init__(self, start: int, end: int, amount: int) -> None:
        self.start, self.end, self.remaining = start, end, amount


class Ledger:
    """Time-ordered ledger: every call's time is >= the previous call's.
    (add_credit's time is its start.) That invariant is what lets
    `_expire` discard grants permanently."""

    def __init__(self) -> None:
        self._heap: list[tuple[int, int, _Grant]] = []   # (end, insertion_idx, grant)
        self._n = 0

    def add_credit(self, start: int, end: int, amount: int) -> None:
        heapq.heappush(self._heap, (end, self._n, _Grant(start, end, amount)))
        self._n += 1

    def _expire(self, t: int) -> None:
        while self._heap and self._heap[0][0] < t:
            heapq.heappop(self._heap)

    def subtract_credit(self, t: int, amount: int) -> int:
        """Spend from the earliest-expiring active grant first. Returns the
        amount actually spent (less than `amount` if credit runs out)."""
        self._expire(t)
        spent = 0
        # Grants in the heap all have start <= t (time-ordered calls) and
        # end >= t (just expired the rest), so the heap top is active.
        while amount > 0 and self._heap:
            end, idx, g = self._heap[0]
            take = min(g.remaining, amount)
            g.remaining -= take
            amount -= take
            spent += take
            if g.remaining == 0:
                heapq.heappop(self._heap)
        return spent

    def check_credit(self, t: int) -> int:
        self._expire(t)
        return sum(g.remaining for _, _, g in self._heap)


# ---------------------------------------------------------------- Parts 1 to 3

_ADD, _SUB = "add", "sub"


class CreditTracker:
    """Events are kept sorted by (timestamp, insertion order). check_credit
    replays the prefix with timestamp <= t through a fresh Ledger. A live
    Ledger mirrors the replay of the whole event list for as long as events
    keep arriving in time order (Parts 1 and 2), so that subtract_credit can
    answer how much it spent without a replay."""

    def __init__(self) -> None:
        self._events: list[tuple[int, int, str, tuple]] = []   # (ts, seq, kind, args)
        self._seq = 0
        self._live = Ledger()          # replay of self._events[:self._live_n]
        self._live_n = 0

    # ---- recording

    def _record(self, ts: int, kind: str, args: tuple) -> int:
        """Insert the event at its (ts, seq) position; return that position."""
        seq = self._seq
        self._seq += 1
        pos = bisect_right(self._events, (ts, seq))      # after every event with ts' <= ts
        self._events.insert(pos, (ts, seq, kind, args))
        if pos < self._live_n:                           # older than something already applied
            self._live, self._live_n = Ledger(), 0       # the live replay is stale: rebuild lazily
        return pos

    def add_credit(self, start: int, end: int, amount: int) -> None:
        self._record(start, _ADD, (start, end, amount))

    def subtract_credit(self, t: int, amount: int) -> int:
        pos = self._record(t, _SUB, (amount,))
        if pos != len(self._events) - 1:
            return 0                   # out of order: recorded; see check_credit
        self._advance_live(pos)        # apply any events recorded since the live ledger stopped
        self._live_n = pos + 1
        return self._live.subtract_credit(t, amount)

    # ---- replay

    @staticmethod
    def _apply(ledger: Ledger, events) -> bool:
        """Apply events (already sorted) to `ledger`; True if any subtraction
        was short."""
        short = False
        for ts, _, kind, args in events:
            if kind == _ADD:
                ledger.add_credit(*args)
            elif ledger.subtract_credit(ts, args[0]) < args[0]:
                short = True
        return short

    def _advance_live(self, upto: int) -> None:
        self._apply(self._live, self._events[self._live_n:upto])
        self._live_n = upto

    def check_credit(self, t: int) -> int:
        """Balance at t after replaying every event with timestamp <= t in
        (timestamp, insertion) order; -1 if any of those subtractions was
        short. O(n log n) per call, as a pure function of (events, t)."""
        k = bisect_right(self._events, (t, self._seq))   # every event with ts <= t
        ledger = Ledger()
        if self._apply(ledger, self._events[:k]):
            return -1
        return ledger.check_credit(t)


if __name__ == "__main__":
    # part 1
    c = CreditTracker()
    c.add_credit(1, 10, 100); c.add_credit(5, 7, 50)
    assert [c.check_credit(t) for t in (0, 1, 5, 7, 8, 11)] == [0, 100, 150, 150, 100, 0]
    c.add_credit(3, 3, 7)
    assert c.check_credit(3) == 107

    # part 2: earliest-expiry-first, proven by the balance AFTER it expires
    c = CreditTracker()
    c.add_credit(1, 10, 100); c.add_credit(5, 7, 50)
    assert c.subtract_credit(6, 70) == 70          # 50 from (5..7), 20 from (1..10)
    assert c.check_credit(6) == 80
    assert c.check_credit(8) == 80                 # (5..7) gone; (1..10) still has 80
    assert c.subtract_credit(8, 500) == 80         # partial
    assert c.subtract_credit(9, 1) == 0            # nothing left
    c = CreditTracker()
    assert c.subtract_credit(1, 5) == 0            # nothing active (short, but records 0 spent)
    c = CreditTracker()
    c.add_credit(1, 3, 10)
    assert c.subtract_credit(3, 4) == 4            # inclusive end
    assert c.check_credit(3) == 6
    assert c.check_credit(4) == 0
    L = Ledger()                                   # tie on end: first added first
    L.add_credit(1, 5, 10); L.add_credit(1, 5, 10)
    assert L.subtract_credit(2, 4) == 4
    assert L._heap[0][2].remaining == 6 and L._heap[1][2].remaining == 10

    # part 3: any order
    C = CreditTracker()
    C.subtract_credit(6, 70)
    assert C.check_credit(6) == -1                 # nothing to cover it yet
    C.add_credit(1, 10, 100)
    assert C.check_credit(6) == 30
    assert C.check_credit(5) == 100                # the subtraction is in the future
    C.add_credit(5, 7, 50)
    assert C.check_credit(6) == 80                 # same replay as the Part 2 example
    assert C.check_credit(8) == 80
    C.subtract_credit(11, 1)                       # (1..10) has expired at 11
    assert C.check_credit(10) == 80
    assert C.check_credit(11) == -1
    assert C.check_credit(0) == 0
    # same timestamp: insertion order decides; add then sub is covered
    C = CreditTracker()
    C.add_credit(2, 2, 5); C.subtract_credit(2, 5)
    assert C.check_credit(2) == 0
    C = CreditTracker()
    C.subtract_credit(2, 5); C.add_credit(2, 2, 5)
    assert C.check_credit(2) == -1
    # the live ledger recovers after an out-of-order event
    C = CreditTracker()
    C.add_credit(5, 9, 10)
    C.add_credit(1, 3, 10)                         # older than the add already applied? nothing applied yet
    assert C.subtract_credit(6, 4) == 4            # in order: exact
    C.add_credit(2, 8, 100)                        # out of order: invalidates the live ledger
    assert C.subtract_credit(7, 10) == 10          # in order again: live ledger rebuilt lazily
    assert C.check_credit(7) == 96

    print("credit_tracker reference OK")
