"""
Per-user execution quotas (SOLVARY_DESIGN.md §6.6 — non-negotiable).

In-memory sliding window + concurrency count. Known limitation (§3.1):
resets on restart and is wrong under multi-instance; migrates behind the
backplane interface when Redis lands.
"""

import time
from collections import defaultdict, deque

from app.core.exceptions import AppException


class RateLimitedException(AppException):
    def __init__(self, detail: str = "Too many execution requests"):
        super().__init__(status_code=429, detail=detail, error_code="RATE_LIMITED")


class QuotaTracker:
    def __init__(self, rate_per_min: int, max_concurrent: int) -> None:
        self._rate_per_min = rate_per_min
        self._max_concurrent = max_concurrent
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._active: dict[str, int] = defaultdict(int)

    def check_and_reserve(self, user_id: str) -> None:
        """Raises RateLimitedException; on success reserves a concurrency slot
        that MUST be released via release() when the job finishes."""
        now = time.monotonic()
        window = self._windows[user_id]
        while window and now - window[0] > 60.0:
            window.popleft()

        if len(window) >= self._rate_per_min:
            raise RateLimitedException(
                f"Rate limit exceeded: {self._rate_per_min} executions per minute"
            )
        if self._active[user_id] >= self._max_concurrent:
            raise RateLimitedException(
                f"Too many concurrent executions (max {self._max_concurrent})"
            )

        window.append(now)
        self._active[user_id] += 1

    def release(self, user_id: str) -> None:
        if self._active[user_id] > 0:
            self._active[user_id] -= 1
