from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

_engine_kwargs: dict = {}
if settings.db_null_pool:
    # Tests: a fresh connection per checkout — pooled async connections are
    # bound to the event loop that created them, and pytest gives each test
    # its own loop
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    # SQLite: the judge worker writes from background tasks concurrently with
    # request sessions; without a busy timeout a held write lock raises
    # "database is locked" immediately
    connect_args={"timeout": 30} if _is_sqlite else {},
    # For PostgreSQL in production, tune these:
    # pool_size=20,
    # max_overflow=10,
    # pool_timeout=30,
    **_engine_kwargs,
)

if _is_sqlite:

    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        """WAL lets readers proceed under a writer; busy_timeout queues writers;
        foreign_keys makes ON DELETE CASCADE actually fire (SQLite ignores FKs
        by default — Postgres enforces them, so this keeps dev honest)."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session():
    """FastAPI dependency that yields a DB session and ensures cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
