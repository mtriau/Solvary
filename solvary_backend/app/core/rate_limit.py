"""
Auth-endpoint rate limiting: sliding windows keyed by client IP and (for
login) the target email — a credential-stuffing attempt against one account
can't be laundered through many IPs, and one IP can't spray many accounts.

Backend follows `queue_backend` (same switch as the execution quota):
  - "memory": per-process deques — fine for a single instance
  - "redis":  sorted-set windows shared by every replica, so limits hold
    under `--scale backend=N`
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque

from fastapi import Request

from app.config import get_settings
from app.core.exceptions import AppException

_REDIS_PREFIX = "solvary:authrl:"


class TooManyRequestsException(AppException):
    def __init__(self, detail: str = "Too many attempts, slow down"):
        super().__init__(status_code=429, detail=detail, error_code="RATE_LIMITED")


class BaseRateLimiter(ABC):
    @abstractmethod
    async def check(self, key: str) -> None:
        """Record a hit; raises TooManyRequestsException when over the limit."""
        ...

    @abstractmethod
    async def reset(self) -> None:
        """Test hook: forget every window this limiter owns."""
        ...


class SlidingWindowLimiter(BaseRateLimiter):
    def __init__(self, limit: int, window_s: float) -> None:
        self._limit = limit
        self._window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def check(self, key: str) -> None:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > self._window_s:
            window.popleft()
        if len(window) >= self._limit:
            raise TooManyRequestsException()
        window.append(now)

    async def reset(self) -> None:
        self._hits.clear()


class RedisSlidingWindowLimiter(BaseRateLimiter):
    """One sorted set per key: members are hit timestamps, trimmed to the
    window on every check. Same shape as RedisQuotaTracker's rate window."""

    def __init__(self, name: str, limit: int, window_s: float) -> None:
        from app.core.redis import get_redis

        self._redis = get_redis()
        self._prefix = f"{_REDIS_PREFIX}{name}:"
        self._limit = limit
        self._window_s = window_s

    async def check(self, key: str) -> None:
        redis_key = f"{self._prefix}{key}"
        now = time.time()
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(redis_key, "-inf", now - self._window_s)
        pipe.zcard(redis_key)
        _, in_window = await pipe.execute()
        if in_window >= self._limit:
            raise TooManyRequestsException()
        pipe = self._redis.pipeline()
        pipe.zadd(redis_key, {f"{now}": now})
        pipe.expire(redis_key, int(self._window_s) + 1)
        await pipe.execute()

    async def reset(self) -> None:
        keys = [k async for k in self._redis.scan_iter(match=f"{self._prefix}*")]
        if keys:
            await self._redis.delete(*keys)


def _make_limiter(name: str, limit: int, window_s: float) -> BaseRateLimiter:
    if get_settings().queue_backend == "redis":
        return RedisSlidingWindowLimiter(name, limit, window_s)
    return SlidingWindowLimiter(limit, window_s)


# Login: 10 attempts / 5 min per (IP, email) + 30 / 5 min per IP overall
login_limiter = _make_limiter("login", limit=10, window_s=300)
login_ip_limiter = _make_limiter("login-ip", limit=30, window_s=300)
# Register + google: 20 / 5 min per IP
signup_limiter = _make_limiter("signup", limit=20, window_s=300)
# AI assistant: 20 questions / min per user (each one is an LLM call)
assist_limiter = _make_limiter("assist", limit=20, window_s=60)
# Interviewer agent: 40 turns / min per user (speech turns are frequent;
# event turns are coalesced client-side) + 5 key tests / min
interviewer_limiter = _make_limiter("interviewer", limit=40, window_s=60)
ai_key_test_limiter = _make_limiter("ai-key-test", limit=5, window_s=60)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
