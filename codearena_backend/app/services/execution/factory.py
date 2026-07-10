"""Executor factory — same shape as create_llm_service."""

from app.config import Settings
from app.services.execution.base import BaseExecutor
from app.services.execution.mock_executor import MockExecutor


def create_executor(settings: Settings) -> BaseExecutor:
    if settings.execution_provider == "mock":
        return MockExecutor()
    if settings.execution_provider == "judge0":
        # M2: Judge0Executor(settings.judge0_base_url, settings.judge0_auth_token)
        raise NotImplementedError("Judge0 executor lands in M2")
    raise ValueError(f"Unknown execution provider: {settings.execution_provider}")
