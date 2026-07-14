"""
Per-user execution quotas (design §6.6 — non-negotiable).

With the Redis queue, a job is reserved on the API instance that accepted
it but released by whichever worker instance finished it — so the counters
MUST be shared. RedisQuotaTracker does that; the in-memory tracker remains
for single-instance deploys.
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque

from app.core.exceptions import AppException


class RateLimitedException(AppException):
    def __init__(self, detail: str = "Too many execution requests"):
        super().__init__(status_code=429, detail=detail, error_code="RATE_LIMITED")


class BaseQuotaTracker(ABC):
    @abstractmethod
    async def check_and_reserve(self, user_id: str) -> None:
        """Raises RateLimitedException; on success reserves a concurrency
        slot that MUST be released via release() when the job finishes."""
        ...

    @abstractmethod
    async def release(self, user_id: str) -> None: ...


class InMemoryQuotaTracker(BaseQuotaTracker):
    def __init__(self, rate_per_min: int, max_concurrent: int) -> None:
        self._rate_per_min = rate_per_min
        self._max_concurrent = max_concurrent
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._active: dict[str, int] = defaultdict(int)

    async def check_and_reserve(self, user_id: str) -> None:
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

    async def release(self, user_id: str) -> None:
        if self._active[user_id] > 0:
            self._active[user_id] -= 1


class RedisQuotaTracker(BaseQuotaTracker):
    def __init__(self, rate_per_min: int, max_concurrent: int) -> None:
        from app.core.redis import get_redis

        self._redis = get_redis()
        self._rate_per_min = rate_per_min
        self._max_concurrent = max_concurrent

    async def check_and_reserve(self, user_id: str) -> None:
        rate_key = f"solvary:rate:{user_id}"
        active_key = f"solvary:active:{user_id}"
        now = time.time()

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(rate_key, "-inf", now - 60.0)
        pipe.zcard(rate_key)
        _, in_window = await pipe.execute()
        if in_window >= self._rate_per_min:
            raise RateLimitedException(
                f"Rate limit exceeded: {self._rate_per_min} executions per minute"
            )

        active = await self._redis.incr(active_key)
        # Safety TTL: a crashed worker can't wedge a user forever
        await self._redis.expire(active_key, 900)
        if active > self._max_concurrent:
            await self._redis.decr(active_key)
            raise RateLimitedException(
                f"Too many concurrent executions (max {self._max_concurrent})"
            )

        pipe = self._redis.pipeline()
        pipe.zadd(rate_key, {f"{now}:{active}": now})
        pipe.expire(rate_key, 120)
        await pipe.execute()

    async def release(self, user_id: str) -> None:
        active_key = f"solvary:active:{user_id}"
        value = await self._redis.decr(active_key)
        if value < 0:  # release without reserve (crash recovery) — clamp
            await self._redis.set(active_key, 0, keepttl=True)
