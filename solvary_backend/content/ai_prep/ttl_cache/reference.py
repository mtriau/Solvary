from __future__ import annotations

import heapq
from collections import OrderedDict


class TTLCache:
    """Entries live in an OrderedDict (recency); a min-heap finds expiries without scanning.

    Overwrites and deletes leave stale heap records. Each entry carries a version, and a
    popped record only counts if its version still matches the live entry for that key.
    """

    def __init__(self, capacity: int | None = None) -> None:
        if capacity is not None and capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        # key -> (value, expires_at, version); order is least -> most recently used.
        self._entries: OrderedDict[str, tuple[object, int, int]] = OrderedDict()
        # (expires_at, version, key); a record is stale unless it matches the entry.
        self._heap: list[tuple[int, int, str]] = []
        self._version = 0
        self._evictions = 0

    def put(self, key: str, value, ttl: int, now: int) -> None:
        """Replace value and TTL; only a brand-new key can trigger eviction."""
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        if value is None:
            raise ValueError("None is not a valid value")
        self._drop_if_expired(key, now)
        if key not in self._entries and self._capacity is not None:
            if len(self._entries) >= self._capacity:
                self.cleanup(now)
            if len(self._entries) >= self._capacity:
                self._entries.popitem(last=False)
                self._evictions += 1
        self._version += 1
        expires_at = now + ttl
        self._entries[key] = (value, expires_at, self._version)
        self._entries.move_to_end(key)
        heapq.heappush(self._heap, (expires_at, self._version, key))

    def get(self, key: str, now: int):
        """Live value (and mark it most recently used) or None."""
        if self._drop_if_expired(key, now) or key not in self._entries:
            return None
        self._entries.move_to_end(key)
        return self._entries[key][0]

    def delete(self, key: str, now: int) -> bool:
        live = not self._drop_if_expired(key, now) and key in self._entries
        self._entries.pop(key, None)
        return live

    def size(self, now: int) -> int:
        """Number of live entries."""
        self.cleanup(now)
        return len(self._entries)

    def cleanup(self, now: int) -> int:
        """Pop every record due by now; O(k log n) for k records, stale ones included."""
        removed = 0
        while self._heap and self._heap[0][0] <= now:
            _, version, key = heapq.heappop(self._heap)
            entry = self._entries.get(key)
            if entry is not None and entry[2] == version:
                del self._entries[key]
                removed += 1
        return removed

    def expiring_before(self, t: int, now: int) -> list[str]:
        live = [(exp, key) for key, (_, exp, _) in self._entries.items() if now < exp < t]
        return [key for _, key in sorted(live)]

    def evictions(self) -> int:
        return self._evictions

    def keys(self, now: int) -> list[str]:
        """Live keys, least to most recently used."""
        self.cleanup(now)
        return list(self._entries)

    def _drop_if_expired(self, key: str, now: int) -> bool:
        """Remove the key if its entry is expired; True when something was removed."""
        entry = self._entries.get(key)
        if entry is not None and entry[1] <= now:
            del self._entries[key]
            return True
        return False
