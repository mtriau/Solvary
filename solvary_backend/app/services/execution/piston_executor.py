"""
PistonExecutor — real sandboxed execution via a self-hosted Piston engine
(deploy/piston/docker-compose.yml). Amended design decision #5 (v2.1):
Piston is cgroup-v2-native, unlike Judge0's isolate.

Piston runs each case in its own isolated process tree with wall/CPU time
and memory caps; it returns raw stdout — checking stays in the worker,
per the executor/worker division in base.py.
"""

import logging
from collections.abc import AsyncIterator

import httpx

from app.services.execution import pytest_harness, python_prelude
from app.services.execution.base import BaseExecutor, ExecEvent, ExecJob

logger = logging.getLogger(__name__)

# Piston run.status → our case status ("finished" means: check the output)
_STATUS_MAP = {
    "TO": "tle",
    "ML": "mle",
    "OL": "runtime_error",  # output limit exceeded
    "XX": "runtime_error",  # internal sandbox error
}

# job.language → piston language name (node package registers as "javascript")
_LANGUAGE_MAP = {
    "python": "python",
    "javascript": "javascript",
}


class PistonExecutor(BaseExecutor):
    def __init__(self, base_url: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport  # tests inject a fake Piston

    async def execute(self, job: ExecJob) -> AsyncIterator[ExecEvent]:
        language = _LANGUAGE_MAP.get(job.language)
        if language is None:
            yield ExecEvent(
                kind="error",
                status="internal_error",
                message=f"No Piston mapping for language '{job.language}'",
            )
            return

        yield ExecEvent(kind="compiling")

        async with httpx.AsyncClient(base_url=self._base_url, transport=self._transport) as client:
            if job.mode == "judge" and job.harness:
                async for event in self._execute_pytest(client, language, job):
                    yield event
                return

            if job.mode == "run" and job.harness:
                async for event in self._execute_pytest_run(client, language, job):
                    yield event
                return

            if job.mode == "run":
                yield ExecEvent(kind="case_started", ordinal=1)
                yield await self._execute_case(
                    client,
                    language,
                    job.code,
                    job.stdin,
                    job.time_limit_s,
                    job.memory_kb,
                    ordinal=1,
                )
                return

            for case in job.cases:
                time_limit = case.time_limit_s or job.time_limit_s
                memory_kb = case.memory_kb or job.memory_kb
                yield ExecEvent(kind="case_started", ordinal=case.ordinal)
                event = await self._execute_case(
                    client,
                    language,
                    job.code,
                    case.stdin,
                    time_limit,
                    memory_kb,
                    ordinal=case.ordinal,
                )
                yield event
                # Compile errors are per-job, not per-case: surface once and stop
                if event.kind == "error":
                    return

    async def _execute_pytest(
        self, client: httpx.AsyncClient, language: str, job: ExecJob
    ) -> AsyncIterator[ExecEvent]:
        """One sandbox run for the whole provided suite, fanned out per case."""
        per_test = min((c.time_limit_s for c in job.cases if c.time_limit_s), default=None)
        data = await self._post(
            client,
            language,
            pytest_harness.build_files(job, per_test),
            pytest_harness.stdin_for(job.cases),
            job.time_limit_s,
            job.memory_kb,
        )
        compile_stage = data.get("compile")
        if compile_stage and compile_stage.get("code") not in (0, None):
            yield ExecEvent(
                kind="error",
                status="compile_error",
                message=(compile_stage.get("stderr") or "")[-2000:],
            )
            return

        run = data.get("run") or {}
        parsed = pytest_harness.parse_output(run.get("stdout") or "")
        if parsed.compile_error is not None:
            yield ExecEvent(
                kind="error", status="compile_error", message=parsed.compile_error[-2000:]
            )
            return

        memory_bytes = run.get("memory")
        mem_kb = int(memory_bytes) // 1024 if memory_bytes else None
        run_status = _STATUS_MAP.get(run.get("status") or "")
        stderr_tail = (run.get("stderr") or "")[-2000:]
        died = run_status is not None or run.get("signal") or run.get("code") not in (0, None)

        for case in job.cases:
            yield ExecEvent(kind="case_started", ordinal=case.ordinal)
            record = parsed.records.get(case.stdin.strip())
            if record is None:
                # The run ended before this test reported: the suite as a
                # whole timed out, crashed, or was cut off by an earlier test
                if run_status == "tle":
                    status, message = "tle", "the suite did not finish within the time limit"
                elif died:
                    status = run_status or "runtime_error"
                    message = stderr_tail or "the test process exited early"
                else:
                    status, message = "runtime_error", "no result reported for this test"
                yield ExecEvent(
                    kind="case_result",
                    ordinal=case.ordinal,
                    status=status,
                    memory_kb=mem_kb,
                    message=message,
                )
                continue
            if record.status == "TLE":
                yield ExecEvent(
                    kind="case_result",
                    ordinal=case.ordinal,
                    status="tle",
                    runtime_ms=record.runtime_ms,
                    memory_kb=mem_kb,
                    message=record.detail,
                )
                continue
            yield ExecEvent(
                kind="case_result",
                ordinal=case.ordinal,
                status="finished",
                runtime_ms=record.runtime_ms,
                memory_kb=mem_kb,
                stdout=pytest_harness.case_stdout(record),
            )

    async def _execute_pytest_run(
        self, client: httpx.AsyncClient, language: str, job: ExecJob
    ) -> AsyncIterator[ExecEvent]:
        """Ad-hoc Run on a pytest-mode problem: run the test ids listed in stdin
        (blank → the whole suite) and hand back one transcript — status per test,
        tracebacks, and whatever the code printed, passing tests included."""
        requested = pytest_harness.requested_ids(job.stdin) or pytest_harness.all_test_ids(
            job.harness or {}
        )
        yield ExecEvent(kind="case_started", ordinal=1)
        data = await self._post(
            client,
            language,
            pytest_harness.build_files(job, always_capture=True),
            "".join(tid + "\n" for tid in requested),
            job.time_limit_s,
            job.memory_kb,
        )
        run = data.get("run") or {}
        parsed = pytest_harness.parse_output(run.get("stdout") or "")
        if parsed.compile_error is not None:
            yield ExecEvent(
                kind="error", status="compile_error", message=parsed.compile_error[-2000:]
            )
            return
        memory_bytes = run.get("memory")
        mem_kb = int(memory_bytes) // 1024 if memory_bytes else None
        run_status = _STATUS_MAP.get(run.get("status") or "")
        transcript = pytest_harness.format_run_output(requested, parsed)
        stderr_tail = (run.get("stderr") or "")[-2000:]
        if run_status == "tle":
            status, message = "tle", "the run did not finish within the time limit"
        elif run_status or run.get("signal") or run.get("code") not in (0, None):
            status, message = (
                run_status or "runtime_error",
                stderr_tail or "the test process exited early",
            )
        else:
            status, message = "finished", stderr_tail or None
        yield ExecEvent(
            kind="case_result",
            ordinal=1,
            status=status,
            runtime_ms=run.get("cpu_time"),
            memory_kb=mem_kb,
            stdout=transcript,
            message=message,
        )

    async def _post(
        self,
        client: httpx.AsyncClient,
        language: str,
        files: list[dict],
        stdin: str,
        time_limit_s: float,
        memory_kb: int,
    ) -> dict:
        payload = {
            "language": language,
            "version": "*",
            "files": files,
            "stdin": stdin,
            "run_timeout": int(time_limit_s * 1000),
            # Piston also caps CPU time separately (default 3 s): a busy loop in one
            # test would otherwise kill the whole suite under its wall limit
            "run_cpu_time": int(time_limit_s * 1000),
            "run_memory_limit": memory_kb * 1024,  # piston takes bytes
        }
        response = await client.post("/api/v2/execute", json=payload, timeout=time_limit_s + 30.0)
        response.raise_for_status()
        return response.json()

    async def _execute_case(
        self,
        client: httpx.AsyncClient,
        language: str,
        code: str,
        stdin: str,
        time_limit_s: float,
        memory_kb: int,
        ordinal: int,
    ) -> ExecEvent:
        # Python scripts run through a tiny runner that preloads the common
        # stdlib names first (python_prelude.py); other languages run as-is
        files = python_prelude.script_files(code) if language == "python" else [{"content": code}]
        data = await self._post(client, language, files, stdin, time_limit_s, memory_kb)

        compile_stage = data.get("compile")
        if compile_stage and compile_stage.get("code") not in (0, None):
            return ExecEvent(
                kind="error",
                status="compile_error",
                message=(compile_stage.get("stderr") or "")[-2000:],
            )

        run = data.get("run") or {}
        cpu_ms = run.get("cpu_time")
        memory_bytes = run.get("memory")
        runtime_ms = int(cpu_ms) if cpu_ms is not None else None
        mem_kb = int(memory_bytes) // 1024 if memory_bytes else None

        status = _STATUS_MAP.get(run.get("status") or "")
        if status is None:
            if run.get("signal"):
                # Killed without a Piston status: MLE only if reported memory
                # actually approached the cap; otherwise a plain kill
                # (sandbox denial, signal from the program itself, …)
                limit_bytes = memory_kb * 1024
                near_cap = (
                    memory_bytes is not None
                    and limit_bytes > 0
                    and memory_bytes >= int(limit_bytes * 0.95)
                )
                status = "mle" if near_cap else "runtime_error"
            elif run.get("code") != 0:
                status = "runtime_error"
            else:
                status = "finished"

        return ExecEvent(
            kind="case_result",
            ordinal=ordinal,
            status=status,
            runtime_ms=runtime_ms,
            memory_kb=mem_kb,
            stdout=run.get("stdout") or "",
            message=(run.get("stderr") or "")[-2000:] or None,
        )
