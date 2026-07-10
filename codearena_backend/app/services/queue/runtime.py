"""
Execution runtime — owns the queue, broker, quota tracker, and worker tasks.

A module-level singleton (same idiom as get_settings). start()/stop() are
called from the app lifespan; start() re-creates the queue and workers in the
CURRENT event loop so tests can start/stop it per-test.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from app.config import Settings, get_settings
from app.services.execution.base import BaseExecutor
from app.services.execution.factory import create_executor
from app.services.queue.broker import EventBroker
from app.services.queue.job_queue import BaseJobQueue, InMemoryJobQueue
from app.services.queue.quota import QuotaTracker
from app.services.queue.worker import JudgeWorker

logger = logging.getLogger(__name__)

_N_WORKERS = 2


def _make_repo_provider(settings: Settings):
    """Async-context-manager factory yielding a SubmissionRepository —
    the worker's DB access, independent of request-scoped DI."""
    if settings.use_mock_db:
        from app.repositories.mock_registry import mock_submission_repo

        @asynccontextmanager
        async def mock_provider():
            yield mock_submission_repo

        return mock_provider

    @asynccontextmanager
    async def sqlalchemy_provider():
        from app.db.engine import async_session_factory
        from app.repositories.sqlalchemy_submission_repository import (
            SQLAlchemySubmissionRepository,
        )

        async with async_session_factory() as session:
            try:
                yield SQLAlchemySubmissionRepository(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return sqlalchemy_provider


class ExecutionRuntime:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.queue: BaseJobQueue = InMemoryJobQueue()
        self.broker = EventBroker()
        self.quota = QuotaTracker(
            rate_per_min=settings.execution_user_rate_per_min,
            max_concurrent=settings.execution_user_concurrency,
        )
        self.executor: BaseExecutor = create_executor(settings)
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        if self._tasks:
            return
        # Fresh queue/broker bound to the current event loop (test-friendly)
        self.queue = InMemoryJobQueue()
        self.broker = EventBroker()
        worker = JudgeWorker(
            queue=self.queue,
            broker=self.broker,
            executor=self.executor,
            repo_provider=_make_repo_provider(self._settings),
            quota=self.quota,
        )
        self._tasks = [
            asyncio.create_task(worker.run(), name=f"judge-worker-{i}")
            for i in range(_N_WORKERS)
        ]
        logger.info("Execution runtime started (%d workers, provider=%s)",
                    _N_WORKERS, self._settings.execution_provider)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks = []
        logger.info("Execution runtime stopped")


_runtime: ExecutionRuntime | None = None


def get_runtime() -> ExecutionRuntime:
    global _runtime
    if _runtime is None:
        _runtime = ExecutionRuntime(get_settings())
    return _runtime
