"""
Judge worker — consumes the job queue and drives the executor.

Runs as async task(s) in the API process for M1–M2: the EXECUTOR is the
isolation boundary (§1.3), not the worker's process boundary. This module is
shaped to run standalone (own repos via provider, no request coupling) if a
local-execution provider ever exists.

Responsibilities (the executor never does these):
  - apply checkers to raw case output → passed/failed
  - verdict semantics (§6.3): cases run samples-first; the first failing
    case's status is the aggregate verdict; remaining hidden cases are
    skipped, remaining samples still run
  - persist submissions INCREMENTALLY (running → per-case appends → final),
    which is what makes SSE replay-then-follow (§6.4) work
  - publish client-facing events (hidden-case stdout stripped)
"""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from app.repositories.submission_repository import SubmissionRepository
from app.services.execution.base import BaseExecutor, ExecEvent, ExecJob
from app.services.execution.checkers import run_checker
from app.services.queue.broker import BaseEventBroker
from app.services.queue.job_queue import BaseJobQueue
from app.services.queue.quota import BaseQuotaTracker

logger = logging.getLogger(__name__)

# Maps a case-level failure status to the aggregate verdict
_FAILURE_VERDICTS = {
    "failed": "wrong_answer",
    "tle": "tle",
    "mle": "mle",
    "runtime_error": "runtime_error",
}

RepoProvider = Callable[[], AbstractAsyncContextManager[SubmissionRepository]]


class JudgeWorker:
    def __init__(
        self,
        queue: BaseJobQueue,
        broker: BaseEventBroker,
        executor: BaseExecutor,
        repo_provider: RepoProvider,
        quota: BaseQuotaTracker,
    ) -> None:
        self._queue = queue
        self._broker = broker
        self._executor = executor
        self._repo_provider = repo_provider
        self._quota = quota

    async def run(self) -> None:
        while True:
            job = await self._queue.dequeue()
            try:
                await self._process(job)
            except Exception:
                logger.exception("Job %s failed with internal error", job.id)
                await self._finalize_internal_error(job)
            finally:
                await self._quota.release(job.user_id)

    # ── processing ─────────────────────────────────────────────────

    async def _process(self, job: ExecJob) -> None:
        if job.mode == "judge":
            await self._process_judge(job)
        else:
            await self._process_run(job)

    async def _process_run(self, job: ExecJob) -> None:
        """Ad-hoc run: pass events through; no checking, no persistence."""
        async for event in self._executor.execute(job):
            if event.kind == "error":
                await self._publish(job, event)
                return
            await self._publish(job, event)
        await self._publish(job, ExecEvent(kind="verdict", verdict="finished"))

    async def _process_judge(self, job: ExecJob) -> None:
        hidden = {c.ordinal for c in job.cases if not c.is_sample}
        case_by_ordinal = {c.ordinal: c for c in job.cases}
        total = len(job.cases)
        results: list[dict] = []
        passed = 0
        failure_verdict: str | None = None
        cases_seen = 0

        await self._persist(job, verdict="running", results=results, passed=passed, total=total)
        await self._publish(job, ExecEvent(kind="queued"))

        agen = self._executor.execute(job)
        try:
            async for event in agen:
                if event.kind == "error":
                    # Compile error (or executor-level failure) before/instead of cases
                    verdict = event.status or "internal_error"
                    if verdict == "compile_error":
                        failure_verdict = "compile_error"
                        await self._publish(job, event)
                        break
                    raise RuntimeError(event.message or "executor error")

                if event.kind != "case_result":
                    await self._publish(job, event, hidden)
                    continue

                # ── a case finished: check it ──────────────────────
                cases_seen += 1
                case = case_by_ordinal.get(event.ordinal or -1)
                status = event.status or "runtime_error"
                if status == "finished" and case is not None:
                    ok = run_checker(
                        case.checker, event.stdout or "", case.expected_stdout, case.checker_args
                    )
                    status = "passed" if ok else "failed"

                event.status = status
                results.append(
                    {
                        "ordinal": event.ordinal,
                        "status": status,
                        "runtime_ms": event.runtime_ms,
                        "memory_kb": event.memory_kb,
                    }
                )
                if status == "passed":
                    passed += 1
                elif failure_verdict is None:
                    failure_verdict = _FAILURE_VERDICTS.get(status, "wrong_answer")

                await self._persist(
                    job, verdict="running", results=results, passed=passed, total=total
                )
                await self._publish(job, event, hidden)

                # §6.3: after a failure, skip remaining hidden cases but let
                # remaining samples run (cases are ordered samples-first)
                if failure_verdict is not None:
                    remaining = job.cases[cases_seen:]
                    if not any(c.is_sample for c in remaining):
                        break
        finally:
            await agen.aclose()

        verdict = failure_verdict or "accepted"
        runtime_ms = max((r["runtime_ms"] or 0 for r in results), default=None)
        memory_kb = max((r["memory_kb"] or 0 for r in results), default=None)

        await self._persist(
            job,
            verdict=verdict,
            results=results,
            passed=passed,
            total=total,
            runtime_ms=runtime_ms,
            memory_kb=memory_kb,
        )
        await self._publish(
            job,
            ExecEvent(
                kind="verdict",
                verdict=verdict,
                passed=passed,
                total=total,
                runtime_ms=runtime_ms,
                memory_kb=memory_kb,
            ),
        )

    # ── helpers ────────────────────────────────────────────────────

    async def _publish(
        self, job: ExecJob, event: ExecEvent, hidden: set[int] | None = None
    ) -> None:
        await self._broker.publish(job.id, event.to_public_dict(hidden))

    async def _persist(
        self,
        job: ExecJob,
        verdict: str,
        results: list[dict],
        passed: int,
        total: int,
        runtime_ms: int | None = None,
        memory_kb: int | None = None,
    ) -> None:
        async with self._repo_provider() as repo:
            submission = await repo.get_by_id(job.id)
            if submission is None:
                logger.warning("Submission %s vanished mid-judge", job.id)
                return
            submission.verdict = verdict  # type: ignore[assignment]
            submission.test_results = list(results)
            submission.passed = passed
            submission.total = total
            if runtime_ms is not None:
                submission.runtime_ms = runtime_ms
            if memory_kb is not None:
                submission.memory_kb = memory_kb
            await repo.update(submission)

    async def _finalize_internal_error(self, job: ExecJob) -> None:
        try:
            if job.mode == "judge":
                async with self._repo_provider() as repo:
                    submission = await repo.get_by_id(job.id)
                    if submission is not None:
                        submission.verdict = "internal_error"
                        await repo.update(submission)
        except Exception:
            logger.exception("Failed to persist internal_error for %s", job.id)
        await self._publish(
            job,
            ExecEvent(kind="error", status="internal_error", message="Internal judge error"),
        )
