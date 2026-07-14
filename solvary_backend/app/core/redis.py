"""Shared async Redis client.

One client per event loop: redis-py connections are bound to the loop that
created them, and pytest gives every test its own loop. In production there
is a single loop, so this degenerates to a plain singleton.
"""

import asyncio

from redis.asyncio import Redis

from app.config import get_settings

_clients: dict[int, Redis] = {}


def _loop_key() -> int:
    """Key clients by the running loop; 0 when called from a sync context
    (e.g. FastAPI sync dependencies in the threadpool) — connections bind
    lazily on first await, so a loop is not needed at construction."""
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        return 0


def get_redis() -> Redis:
    key = _loop_key()
    client = _clients.get(key)
    if client is None:
        client = Redis.from_url(get_settings().redis_url, decode_responses=False)
        _clients[key] = client
    return client


async def close_redis() -> None:
    client = _clients.pop(_loop_key(), None)
    if client is not None:
        await client.aclose()
