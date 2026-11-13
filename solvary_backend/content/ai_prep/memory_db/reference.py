import math


class MemoryDB:
    """Records of string fields. Every field is stored as (value, expires_at),
    alive for timestamps t with t < expires_at; no TTL means expires_at = inf.
    The plain methods are the *_at methods evaluated at the latest timestamp
    seen so far, so each level is an extension of the one before."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, tuple[str, float]]] = {}
        self._now = 0
        self._backups: list[tuple[int, dict[str, dict[str, tuple[str, float]]]]] = []

    # -- Part 1 -----------------------------------------------------

    def set(self, key: str, field: str, value: str) -> None:
        self.set_at(key, field, value, self._now)

    def get(self, key: str, field: str) -> str | None:
        return self.get_at(key, field, self._now)

    def delete(self, key: str, field: str) -> bool:
        return self.delete_at(key, field, self._now)

    # -- Part 2 -----------------------------------------------------

    def scan(self, key: str) -> list[str]:
        return self.scan_at(key, self._now)

    def scan_by_prefix(self, key: str, prefix: str) -> list[str]:
        return self.scan_by_prefix_at(key, prefix, self._now)

    # -- Part 3 -----------------------------------------------------

    def set_at(self, key: str, field: str, value: str, timestamp: int) -> None:
        self.set_at_with_ttl(key, field, value, timestamp, math.inf)

    def set_at_with_ttl(
        self, key: str, field: str, value: str, timestamp: int, ttl: float
    ) -> None:
        self._now = max(self._now, timestamp)
        self._data.setdefault(key, {})[field] = (value, timestamp + ttl)

    def delete_at(self, key: str, field: str, timestamp: int) -> bool:
        self._now = max(self._now, timestamp)
        record = self._data.get(key, {})
        cell = record.pop(field, None)
        if not record:
            self._data.pop(key, None)
        return cell is not None and timestamp < cell[1]

    def get_at(self, key: str, field: str, timestamp: int) -> str | None:
        return self._live(key, timestamp).get(field)

    def scan_at(self, key: str, timestamp: int) -> list[str]:
        return self.scan_by_prefix_at(key, "", timestamp)

    def scan_by_prefix_at(self, key: str, prefix: str, timestamp: int) -> list[str]:
        live = self._live(key, timestamp)
        return [f"{f}({live[f]})" for f in sorted(live) if f.startswith(prefix)]

    def _live(self, key: str, timestamp: int) -> dict[str, str]:
        self._now = max(self._now, timestamp)
        record = self._data.get(key, {})
        return {f: v for f, (v, expires) in record.items() if timestamp < expires}

    # -- Part 4 -----------------------------------------------------

    def backup(self, timestamp: int) -> int:
        """Snapshot the live fields as (value, remaining lifetime)."""
        self._now = max(self._now, timestamp)
        snapshot = {}
        for key, record in self._data.items():
            live = {f: (v, e - timestamp) for f, (v, e) in record.items() if timestamp < e}
            if live:
                snapshot[key] = live
        self._backups.append((timestamp, snapshot))
        return len(snapshot)

    def restore(self, timestamp: int, timestamp_to_restore: int) -> None:
        self._now = max(self._now, timestamp)
        eligible = [b for b in self._backups if b[0] <= timestamp_to_restore]
        if not eligible:
            return
        _, snapshot = max(eligible, key=lambda b: b[0])
        self._data = {
            key: {f: (v, timestamp + remaining) for f, (v, remaining) in record.items()}
            for key, record in snapshot.items()
        }
