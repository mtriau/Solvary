"""
Per-job event pub/sub with history (replay-then-follow, design §6.4).

  - InMemoryEventBroker: single instance — subscribers must be in-process
  - RedisEventBroker: Redis Streams — a client streaming SSE on instance A
    sees events from a worker running on instance B; XRANGE-from-zero gives
    replay, blocking XREAD gives follow, one structure, no race between them

For submissions the DB row remains the durable fallback; ad-hoc runs stay
ephemeral by design (§6.5) — with Redis they just survive a bit longer
(stream TTL) and work cross-instance.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import AsyncIterator

_TERMINAL_KINDS = {"verdict", "error"}
_MAX_COMPLETED_JOBS = 500

_STREAM_PREFIX = "solvary:ev:"
_STREAM_TTL_S = 3600


class BaseEventBroker(ABC):
    @abstractmethod
    async def publish(self, job_id: str, event: dict) -> None: ...

    @abstractmethod
    def subscribe(self, job_id: str) -> AsyncIterator[dict]:
        """Replay history, then follow live until a terminal event."""
        ...

    @abstractmethod
    async def is_done(self, job_id: str) -> bool: ...

    @abstractmethod
    async def known(self, job_id: str) -> bool: ...


class InMemoryEventBroker(BaseEventBroker):
    def __init__(self) -> None:
        self._history: OrderedDict[str, list[dict]] = OrderedDict()
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._done: set[str] = set()

    async def publish(self, job_id: str, event: dict) -> None:
        self._history.setdefault(job_id, []).append(event)
        for queue in self._subscribers.get(job_id, []):
            queue.put_nowait(event)
        if event.get("kind") in _TERMINAL_KINDS:
            self._done.add(job_id)
            self._evict_completed()

    async def is_done(self, job_id: str) -> bool:
        return job_id in self._done

    async def known(self, job_id: str) -> bool:
        return job_id in self._history

    async def subscribe(self, job_id: str) -> AsyncIterator[dict]:
        queue: asyncio.Queue[dict] = asyncio.Queue()
        history = list(self._history.get(job_id, []))
        done = job_id in self._done

        if not done:
            self._subscribers.setdefault(job_id, []).append(queue)

        try:
            for event in history:
                yield event
                if event.get("kind") in _TERMINAL_KINDS:
                    return
            if done:
                return
            while True:
                event = await queue.get()
                yield event
                if event.get("kind") in _TERMINAL_KINDS:
                    return
        finally:
            subs = self._subscribers.get(job_id)
            if subs and queue in subs:
                subs.remove(queue)
                if not subs:
                    self._subscribers.pop(job_id, None)

    def _evict_completed(self) -> None:
        completed = [jid for jid in self._history if jid in self._done]
        while len(completed) > _MAX_COMPLETED_JOBS:
            oldest = completed.pop(0)
            self._history.pop(oldest, None)
            self._done.discard(oldest)


class RedisEventBroker(BaseEventBroker):
    def __init__(self) -> None:
        from app.core.redis import get_redis

        self._redis = get_redis()

    @staticmethod
    def _key(job_id: str) -> str:
        return f"{_STREAM_PREFIX}{job_id}"

    async def publish(self, job_id: str, event: dict) -> None:
        key = self._key(job_id)
        pipe = self._redis.pipeline()
        pipe.xadd(key, {"data": json.dumps(event)}, maxlen=1000, approximate=True)
        pipe.expire(key, _STREAM_TTL_S)
        await pipe.execute()

    async def is_done(self, job_id: str) -> bool:
        entries = await self._redis.xrevrange(self._key(job_id), count=1)
        if not entries:
            return False
        event = json.loads(entries[0][1][b"data"])
        return event.get("kind") in _TERMINAL_KINDS

    async def known(self, job_id: str) -> bool:
        return bool(await self._redis.exists(self._key(job_id)))

    async def subscribe(self, job_id: str) -> AsyncIterator[dict]:
        key = self._key(job_id)
        last_id = "0"
        while True:
            # Replay + follow in one loop: XREAD from the last seen id
            batches = await self._redis.xread({key: last_id}, block=2000, count=100)
            if not batches:
                continue
            for _stream, entries in batches:
                for entry_id, fields in entries:
                    last_id = entry_id.decode() if isinstance(entry_id, bytes) else entry_id
                    event = json.loads(fields[b"data"])
                    yield event
                    if event.get("kind") in _TERMINAL_KINDS:
                        return
