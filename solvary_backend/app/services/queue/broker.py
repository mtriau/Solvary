"""
In-process event broker: per-job pub/sub with bounded history.

The worker publishes client-facing event dicts here; SSE endpoints subscribe.
History means a subscriber that arrives after events fired still sees them
(replay-then-follow) — for submissions the DB row is the durable fallback
across restarts; ad-hoc runs are ephemeral by design (§6.5).
"""

import asyncio
from collections import OrderedDict

_TERMINAL_KINDS = {"verdict", "error"}
_MAX_COMPLETED_JOBS = 500


class EventBroker:
    def __init__(self) -> None:
        self._history: OrderedDict[str, list[dict]] = OrderedDict()
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        self._done: set[str] = set()

    def publish(self, job_id: str, event: dict) -> None:
        self._history.setdefault(job_id, []).append(event)
        for queue in self._subscribers.get(job_id, []):
            queue.put_nowait(event)
        if event.get("kind") in _TERMINAL_KINDS:
            self._done.add(job_id)
            self._evict_completed()

    def is_done(self, job_id: str) -> bool:
        return job_id in self._done

    def known(self, job_id: str) -> bool:
        return job_id in self._history

    async def subscribe(self, job_id: str):
        """Async iterator: replay history, then follow live until terminal."""
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
        """Keep memory bounded: drop oldest completed job histories."""
        completed = [jid for jid in self._history if jid in self._done]
        while len(completed) > _MAX_COMPLETED_JOBS:
            oldest = completed.pop(0)
            self._history.pop(oldest, None)
            self._done.discard(oldest)
