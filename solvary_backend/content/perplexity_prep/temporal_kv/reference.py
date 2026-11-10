"""Ideal solution: Time-Versioned KV Store, all three parts.

Part 1: set(key, value, ts) / get(key, ts): value as of ts (bisect_right).
Part 2: delete(key, ts) is a tombstone (value None) in the same per-key
        list; get_range(key, start, end) is two bisects and a slice.
Part 3: restore(ts) discards every mutation with timestamp > ts across all
        keys by popping the tail of a global mutation log, O(discarded).

Shape an interviewer expects:
  - Per key: parallel lists `ts` and `vals`. Because set/delete timestamps
    are non-decreasing GLOBALLY, appending keeps every per-key list sorted
    and the global log order equals the per-key order.
  - get: bisect_right(ts_list, ts) - 1 lands on the LAST entry with that
    timestamp, which is the later call; that is the "later call wins" rule
    for free.
  - get on an unknown key uses dict.get, never defaultdict indexing, so a
    read can never create state.
  - restore: while log[-1].ts > target, pop the log entry and pop the last
    element of that key's lists (it is always the last, by the invariant).
    Keys left empty are removed so they read as unknown again.
"""

from bisect import bisect_left, bisect_right


class TemporalKV:
    def __init__(self) -> None:
        self._ts: dict[str, list[int]] = {}
        self._vals: dict[str, list[str | None]] = {}
        self._log: list[tuple[int, str]] = []      # (ts, key), global order

    # ------------------------------------------------------------ Part 1

    def set(self, key: str, value: str, ts: int) -> None:
        """O(1) amortized."""
        self._record(key, value, ts)

    def get(self, key: str, ts: int) -> str | None:
        """O(log n) in the number of mutations of `key`."""
        ts_list = self._ts.get(key)
        if not ts_list:
            return None
        i = bisect_right(ts_list, ts)
        return self._vals[key][i - 1] if i else None

    # ------------------------------------------------------------ Part 2

    def delete(self, key: str, ts: int) -> None:
        """Tombstone: O(1) amortized. Allowed on a never-set key."""
        self._record(key, None, ts)

    def get_range(self, key: str, start: int, end: int) -> list[tuple[int, str | None]]:
        """Change points with start <= ts <= end, in call order. O(log n + k)."""
        ts_list = self._ts.get(key)
        if not ts_list or start > end:
            return []
        lo = bisect_left(ts_list, start)
        hi = bisect_right(ts_list, end)
        return list(zip(ts_list[lo:hi], self._vals[key][lo:hi]))

    # ------------------------------------------------------------ Part 3

    def restore(self, ts: int) -> None:
        """Discard every mutation with timestamp > ts. O(discarded)."""
        while self._log and self._log[-1][0] > ts:
            _, key = self._log.pop()
            self._ts[key].pop()
            self._vals[key].pop()
            if not self._ts[key]:
                del self._ts[key]
                del self._vals[key]

    # ------------------------------------------------------------ helpers

    def _record(self, key: str, value: str | None, ts: int) -> None:
        self._ts.setdefault(key, []).append(ts)
        self._vals.setdefault(key, []).append(value)
        self._log.append((ts, key))


if __name__ == "__main__":
    kv = TemporalKV()
    kv.set("a", "1", 1)
    kv.set("a", "2", 5)
    kv.set("b", "x", 5)
    assert kv.get("a", 0) is None
    assert kv.get("a", 1) == "1"
    assert kv.get("a", 3) == "1"
    assert kv.get("a", 5) == "2"
    assert kv.get("a", 100) == "2"
    assert kv.get("b", 4) is None
    assert kv.get("zzz", 5) is None

    kv = TemporalKV()
    kv.set("a", "v", 1)
    kv.delete("a", 5)
    kv.set("a", "w", 9)
    assert [kv.get("a", t) for t in (4, 5, 8, 9)] == ["v", None, None, "w"]
    assert kv.get_range("a", 5, 5) == [(5, None)]
    assert kv.get_range("a", 6, 8) == []
    assert kv.get_range("a", 0, 100) == [(1, "v"), (5, None), (9, "w")]
    assert kv.get_range("a", 9, 1) == []

    kv.restore(3)
    assert kv.get("a", 10) == "v"
    assert kv.get_range("a", 0, 100) == [(1, "v")]
    kv.set("a", "z", 3)
    assert kv.get("a", 3) == "z"
    kv.restore(0)
    assert kv.get("a", 100) is None
    assert kv.get_range("a", 0, 100) == []
    print("OK")
