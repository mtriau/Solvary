import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app
from app.services.queue import runtime as runtime_module
from app.services.queue.runtime import ExecutionRuntime


@pytest.fixture
async def judge_runtime():
    """Fresh execution runtime bound to this test's event loop.

    ASGITransport does not run the app lifespan, so the worker tasks that
    normally start there are started (and torn down) here instead.
    """
    runtime = ExecutionRuntime(get_settings())
    runtime_module._runtime = runtime
    await runtime.start()
    yield runtime
    await runtime.stop()
    runtime_module._runtime = None


@pytest.fixture
async def client(judge_runtime):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
