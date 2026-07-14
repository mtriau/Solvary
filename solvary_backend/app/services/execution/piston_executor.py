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
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

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

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            if job.mode == "run":
                yield ExecEvent(kind="case_started", ordinal=1)
                yield await self._execute_case(
                    client, language, job.code, job.stdin, job.time_limit_s,
                    job.memory_kb, ordinal=1,
                )
                return

            for case in job.cases:
                time_limit = case.time_limit_s or job.time_limit_s
                memory_kb = case.memory_kb or job.memory_kb
                yield ExecEvent(kind="case_started", ordinal=case.ordinal)
                event = await self._execute_case(
                    client, language, job.code, case.stdin, time_limit,
                    memory_kb, ordinal=case.ordinal,
                )
                yield event
                # Compile errors are per-job, not per-case: surface once and stop
                if event.kind == "error":
                    return

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
        payload = {
            "language": language,
            "version": "*",
            "files": [{"content": code}],
            "stdin": stdin,
            "run_timeout": int(time_limit_s * 1000),
            "run_memory_limit": memory_kb * 1024,  # piston takes bytes
        }
        response = await client.post(
            "/api/v2/execute", json=payload, timeout=time_limit_s + 30.0
        )
        response.raise_for_status()
        data = response.json()

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
