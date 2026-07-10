"""
Job queue abstraction. In-process asyncio.Queue for M1–M2 (locked in
CODEARENA_DESIGN.md §11); a Redis-backed implementation arrives with the
Redis backplane in phase 2, behind this same interface.
"""

import asyncio
from abc import ABC, abstractmethod

from app.services.execution.base import ExecJob


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
