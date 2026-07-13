"""Executor factory — same shape as create_llm_service."""

from app.config import Settings
from app.services.execution.base import BaseExecutor
from app.services.execution.mock_executor import MockExecutor


def create_executor(settings: Settings) -> BaseExecutor:
    if settings.execution_provider == "mock":
        return MockExecutor()
    if settings.execution_provider == "piston":
        from app.services.execution.piston_executor import PistonExecutor

        return PistonExecutor(settings.piston_base_url)
    raise ValueError(f"Unknown execution provider: {settings.execution_provider}")
