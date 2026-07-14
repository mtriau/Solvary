"""
MockExecutor — dev/test provider that simulates execution without running code.

Deterministic behavior, steered by magic markers in the submitted code:

  (none)          → every case "succeeds": stdout = the case's expected output
  __MOCK_WA__     → the highest-ordinal case produces wrong output
  __MOCK_TLE__    → the first case times out
  __MOCK_RTE__    → the first case hits a runtime error
  __MOCK_CE__     → compilation fails before any case runs

This makes the full submit → queue → worker → checker → SSE pipeline
demoable and testable end-to-end. Real execution arrives with Judge0 (M2)
behind this same BaseExecutor interface.
"""

import asyncio
from collections.abc import AsyncIterator

from app.services.execution.base import BaseExecutor, ExecEvent, ExecJob


class MockExecutor(BaseExecutor):
    def __init__(self, case_delay_s: float = 0.05) -> None:
        self._case_delay_s = case_delay_s

    async def execute(self, job: ExecJob) -> AsyncIterator[ExecEvent]:
        yield ExecEvent(kind="compiling")
        await asyncio.sleep(self._case_delay_s)

        if "__MOCK_CE__" in job.code:
            yield ExecEvent(
                kind="error",
                status="compile_error",
                message="mock: syntax error on line 1",
            )
            return

        if job.mode == "run":
            # Ad-hoc run: echo stdin back as output
            yield ExecEvent(kind="case_started", ordinal=1)
            await asyncio.sleep(self._case_delay_s)
            yield ExecEvent(
                kind="case_result",
                ordinal=1,
                status="finished",
                runtime_ms=12,
                memory_kb=1024,
                stdout=job.stdin,
            )
            return

        last_ordinal = max((c.ordinal for c in job.cases), default=0)
        for case in job.cases:
            yield ExecEvent(kind="case_started", ordinal=case.ordinal)
            await asyncio.sleep(self._case_delay_s)

            if "__MOCK_TLE__" in job.code and case.ordinal == 1:
                yield ExecEvent(
                    kind="case_result",
                    ordinal=case.ordinal,
                    status="tle",
                    runtime_ms=int(job.time_limit_s * 1000),
                    memory_kb=1024,
                )
                continue

            if "__MOCK_RTE__" in job.code and case.ordinal == 1:
                yield ExecEvent(
                    kind="case_result",
                    ordinal=case.ordinal,
                    status="runtime_error",
                    runtime_ms=8,
                    memory_kb=1024,
                    message="mock: unhandled exception",
                )
                continue

            stdout = case.expected_stdout
            if "__MOCK_WA__" in job.code and case.ordinal == last_ordinal:
                stdout = stdout.rstrip("\n") + " WRONG\n"

            yield ExecEvent(
                kind="case_result",
                ordinal=case.ordinal,
                status="finished",
                runtime_ms=10 + case.ordinal,
                memory_kb=2048,
                stdout=stdout,
            )
