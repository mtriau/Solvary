"""
Room backplane (design §7.3, decision #4): fans collaboration frames out
across instances.

  - InMemoryBackplane: single instance. publish() is a no-op — there are no
    other instances; the manager already broadcast to local sockets.
  - RedisBackplane: pub/sub channel per room. Frames carry an origin
    instance id so publishers skip their own messages; the manager applies
    remote updates to its local room doc and forwards them to local sockets.

Also owns two multi-instance primitives the manager needs:
  - next_seq: DocUpdate sequence allocation (Redis INCR — two instances
    persisting concurrently can't collide with the unique (workspace, seq))
  - try_lock: best-effort lock so only one instance compacts at a time
"""

import asyncio
import base64
import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

# on_remote(kind, payload, seq) — kind: "update" | "awareness" | "files"
RemoteHandler = Callable[[str, bytes, int], Awaitable[None]]

_CHANNEL_PREFIX = "solvary:room:"
_SEQ_PREFIX = "solvary:seq:"
_LOCK_PREFIX = "solvary:lock:"


class BaseBackplane(ABC):
    @abstractmethod
    async def join(self, room: str, on_remote: RemoteHandler) -> None: ...

    @abstractmethod
    async def leave(self, room: str) -> None: ...

    @abstractmethod
    async def publish(self, room: str, kind: str, payload: bytes, seq: int = 0) -> None: ...

    @abstractmethod
    async def next_seq(self, room: str, floor: int) -> int: ...

    @abstractmethod
    async def try_lock(self, name: str, ttl_s: int) -> bool: ...

    async def stop(self) -> None:  # pragma: no cover - default no-op
        return


class InMemoryBackplane(BaseBackplane):
    def __init__(self) -> None:
        self._seq: dict[str, int] = {}

    async def join(self, room: str, on_remote: RemoteHandler) -> None:
        return

    async def leave(self, room: str) -> None:
        return

    async def publish(self, room: str, kind: str, payload: bytes, seq: int = 0) -> None:
        return  # no other instances exist

    async def next_seq(self, room: str, floor: int) -> int:
        current = max(self._seq.get(room, 0), floor) + 1
        self._seq[room] = current
        return current

    async def try_lock(self, name: str, ttl_s: int) -> bool:
        return True


class RedisBackplane(BaseBackplane):
    def __init__(self) -> None:
        from app.core.redis import get_redis

        self._redis = get_redis()
        self._instance_id = uuid.uuid4().hex
        self._handlers: dict[str, RemoteHandler] = {}
        self._pubsub = None
        self._dispatch_task: asyncio.Task | None = None

    async def _ensure_dispatcher(self) -> None:
        if self._pubsub is None:
            self._pubsub = self._redis.pubsub()
            self._dispatch_task = asyncio.create_task(
                self._dispatch(), name="backplane-dispatch"
            )

    async def _dispatch(self) -> None:
        while True:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=2.0
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Backplane dispatch error; retrying")
                await asyncio.sleep(1.0)
                continue
            if message is None:
                continue
            try:
                data = json.loads(message["data"])
                if data["origin"] == self._instance_id:
                    continue
                channel = message["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode()
                room = channel[len(_CHANNEL_PREFIX):]
                handler = self._handlers.get(room)
                if handler is not None:
                    await handler(
                        data["kind"],
                        base64.b64decode(data["payload"]),
                        data.get("seq", 0),
                    )
            except Exception:
                logger.exception("Backplane message handling failed")

    async def join(self, room: str, on_remote: RemoteHandler) -> None:
        await self._ensure_dispatcher()
        self._handlers[room] = on_remote
        await self._pubsub.subscribe(f"{_CHANNEL_PREFIX}{room}")

    async def leave(self, room: str) -> None:
        self._handlers.pop(room, None)
        if self._pubsub is not None:
            await self._pubsub.unsubscribe(f"{_CHANNEL_PREFIX}{room}")

    async def publish(self, room: str, kind: str, payload: bytes, seq: int = 0) -> None:
        await self._redis.publish(
            f"{_CHANNEL_PREFIX}{room}",
            json.dumps(
                {
                    "origin": self._instance_id,
                    "kind": kind,
                    "payload": base64.b64encode(payload).decode(),
                    "seq": seq,
                }
            ),
        )

    async def next_seq(self, room: str, floor: int) -> int:
        key = f"{_SEQ_PREFIX}{room}"
        # Ensure the counter is at least the persisted floor, then INCR
        await self._redis.set(key, floor, nx=True)
        return int(await self._redis.incr(key))

    async def try_lock(self, name: str, ttl_s: int) -> bool:
        return bool(
            await self._redis.set(
                f"{_LOCK_PREFIX}{name}", self._instance_id, nx=True, ex=ttl_s
            )
        )

    async def stop(self) -> None:
        if self._dispatch_task is not None:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        if self._pubsub is not None:
            await self._pubsub.aclose()
