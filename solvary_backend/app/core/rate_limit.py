"""
Auth-endpoint rate limiting: in-memory sliding windows keyed by client IP
and (for login) the target email — a credential-stuffing attempt against
one account can't be laundered through many IPs, and one IP can't spray
many accounts.

Same known limitation as the execution quota (design §3.1): in-memory,
resets on restart, wrong under multi-instance; moves behind the Redis
backplane in phase 2.
"""

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.exceptions import AppException


class TooManyRequestsException(AppException):
    def __init__(self, detail: str = "Too many attempts, slow down"):
        super().__init__(status_code=429, detail=detail, error_code="RATE_LIMITED")


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_s: float) -> None:
        self._limit = limit
        self._window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > self._window_s:
            window.popleft()
        if len(window) >= self._limit:
            raise TooManyRequestsException()
        window.append(now)

    def reset(self) -> None:
        """Test hook."""
        self._hits.clear()


# Login: 10 attempts / 5 min per (IP, email) + 30 / 5 min per IP overall
login_limiter = SlidingWindowLimiter(limit=10, window_s=300)
login_ip_limiter = SlidingWindowLimiter(limit=30, window_s=300)
# Register + google: 20 / 5 min per IP
signup_limiter = SlidingWindowLimiter(limit=20, window_s=300)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
