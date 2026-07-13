import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.middleware.cors import add_cors_middleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    if not settings.use_mock_db:
        # Import tables so they register with Base.metadata
        import app.db.tables  # noqa: F401
        from app.db.base import Base
        from app.db.engine import engine

        logger.info("Creating database tables (if not exist)")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database ready — connected to %s", settings.database_url.split("@")[-1])
    else:
        logger.info("Running in mock mode — no database")

    from app.services.queue.runtime import get_runtime

    runtime = get_runtime()
    await runtime.start()

    logger.info("CodeArena API starting up")
    yield

    await runtime.stop()

    if not settings.use_mock_db:
        from app.db.engine import engine

        await engine.dispose()
        logger.info("Database connections closed")

    logger.info("CodeArena API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Middleware (order matters — outermost first)
    add_cors_middleware(application, settings)
    application.add_middleware(LoggingMiddleware)
    application.add_middleware(RequestIdMiddleware)

    # Exception handlers
    register_exception_handlers(application)

    # Routes
    application.include_router(api_router, prefix=settings.api_prefix)

    # Collaboration WebSocket lives at root (/ws/...), not under /api (design §5)
    from app.api.v1 import ws_collaboration

    application.include_router(ws_collaboration.router)

    return application


app = create_app()
