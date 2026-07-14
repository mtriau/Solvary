"""
Execution runtime — owns the queue, broker, quota tracker, worker tasks,
and the stale-job reaper.

Backends are selected by settings.queue_backend:
  - "memory": single-instance (dev / small deploys)
  - "redis":  queue, event broker, and quota shared across instances —
    any replica's worker can run any job, any replica can serve its SSE

The reaper marks non-terminal submissions with stale updated_at as
internal_error: the worker persists incrementally, so a live job always
has a fresh row — staleness means its worker died (crash, deploy, OOM).
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from app.config import Settings, get_settings
from app.services.execution.base import BaseExecutor
from app.services.execution.factory import create_executor
from app.services.queue.broker import BaseEventBroker, InMemoryEventBroker, RedisEventBroker
from app.services.queue.job_queue import BaseJobQueue, InMemoryJobQueue, RedisJobQueue
from app.services.queue.quota import BaseQuotaTracker, InMemoryQuotaTracker, RedisQuotaTracker
from app.services.queue.worker import JudgeWorker

logger = logging.getLogger(__name__)

_N_WORKERS = 2
_REAPER_INTERVAL_S = 60
_STALE_AFTER = timedelta(minutes=5)


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


def _make_queue(settings: Settings) -> BaseJobQueue:
    if settings.queue_backend == "redis":
        return RedisJobQueue()
    return InMemoryJobQueue()


def _make_broker(settings: Settings) -> BaseEventBroker:
    if settings.queue_backend == "redis":
        return RedisEventBroker()
    return InMemoryEventBroker()


def _make_quota(settings: Settings) -> BaseQuotaTracker:
    cls = RedisQuotaTracker if settings.queue_backend == "redis" else InMemoryQuotaTracker
    return cls(
        rate_per_min=settings.execution_user_rate_per_min,
        max_concurrent=settings.execution_user_concurrency,
    )


class ExecutionRuntime:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.queue: BaseJobQueue = _make_queue(settings)
        self.broker: BaseEventBroker = _make_broker(settings)
        self.quota: BaseQuotaTracker = _make_quota(settings)
        self.executor: BaseExecutor = create_executor(settings)
        self._repo_provider = _make_repo_provider(settings)
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        if self._tasks:
            return
        # Fresh in-memory structures bound to the current event loop
        # (test-friendly); Redis backends are loop-agnostic
        self.queue = _make_queue(self._settings)
        self.broker = _make_broker(self._settings)
        worker = JudgeWorker(
            queue=self.queue,
            broker=self.broker,
            executor=self.executor,
            repo_provider=self._repo_provider,
            quota=self.quota,
        )
        self._tasks = [
            asyncio.create_task(worker.run(), name=f"judge-worker-{i}")
            for i in range(_N_WORKERS)
        ]
        self._tasks.append(asyncio.create_task(self._reaper(), name="job-reaper"))
        logger.info(
            "Execution runtime started (%d workers, provider=%s, backend=%s)",
            _N_WORKERS,
            self._settings.execution_provider,
            self._settings.queue_backend,
        )

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

    async def _reaper(self) -> None:
        while True:
            await asyncio.sleep(_REAPER_INTERVAL_S)
            try:
                await self.reap_stale_jobs()
            except Exception:
                logger.exception("Job reaper pass failed")

    async def reap_stale_jobs(self) -> int:
        """Mark abandoned submissions as internal_error. Idempotent —
        safe to run on every instance."""
        cutoff = datetime.now(UTC) - _STALE_AFTER
        reaped = 0
        async with self._repo_provider() as repo:
            for submission in await repo.find_stale(cutoff):
                submission.verdict = "internal_error"
                await repo.update(submission)
                await self.broker.publish(
                    submission.id,
                    {
                        "kind": "error",
                        "status": "internal_error",
                        "message": "Judge worker lost (instance restarted?) — please resubmit",
                    },
                )
                reaped += 1
        if reaped:
            logger.warning("Reaped %d stale submission(s)", reaped)
        return reaped


_runtime: ExecutionRuntime | None = None


def get_runtime() -> ExecutionRuntime:
    global _runtime
    if _runtime is None:
        _runtime = ExecutionRuntime(get_settings())
    return _runtime
