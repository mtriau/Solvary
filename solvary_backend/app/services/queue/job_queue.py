"""
Job queue abstraction (design decision #6).

  - InMemoryJobQueue: asyncio.Queue, single instance (dev / small deploys)
  - RedisJobQueue: a Redis list shared by every instance — any worker on
    any replica can pick up any job (BLPOP)

Selected by settings.queue_backend.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import asdict

from app.services.execution.base import ExecCase, ExecJob

_REDIS_KEY = "solvary:jobs"


def job_to_json(job: ExecJob) -> str:
    return json.dumps(asdict(job))


def job_from_json(raw: str | bytes) -> ExecJob:
    data = json.loads(raw)
    data["cases"] = [ExecCase(**c) for c in data.get("cases", [])]
    return ExecJob(**data)


class BaseJobQueue(ABC):
    @abstractmethod
    async def enqueue(self, job: ExecJob) -> None: ...

    @abstractmethod
    async def dequeue(self) -> ExecJob: ...


class InMemoryJobQueue(BaseJobQueue):
    def __init__(self) -> None:
        self._queue: asyncio.Queue[ExecJob] = asyncio.Queue()

    async def enqueue(self, job: ExecJob) -> None:
        await self._queue.put(job)

    async def dequeue(self) -> ExecJob:
        return await self._queue.get()


class RedisJobQueue(BaseJobQueue):
    def __init__(self) -> None:
        from app.core.redis import get_redis

        self._redis = get_redis()

    async def enqueue(self, job: ExecJob) -> None:
        await self._redis.rpush(_REDIS_KEY, job_to_json(job))

    async def dequeue(self) -> ExecJob:
        # BLPOP with a timeout so worker tasks stay cancellable
        while True:
            item = await self._redis.blpop(_REDIS_KEY, timeout=2)
            if item is not None:
                return job_from_json(item[1])
