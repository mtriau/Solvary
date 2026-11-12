import heapq
from collections.abc import Iterable, Iterator
from typing import Any

Event = dict[str, Any]


# ── Part 1 ─────────────────────────────────────────────────────────


def merge_streams(streams: list[list[Event]]) -> list[Event]:
    return list(merge_live(streams))


# ── Part 2 ─────────────────────────────────────────────────────────


def merge_live(streams: list[Iterable[Event]]) -> Iterator[Event]:
    # Heap of (ts, stream_index, event, iterator). stream_index is unique, so
    # the comparison never reaches the event dict.
    heap: list[tuple[int, int, Event, Iterator[Event]]] = []
    for i, stream in enumerate(streams):
        it = iter(stream)
        first = next(it, None)
        if first is not None:
            heap.append((first["ts"], i, first, it))
    heapq.heapify(heap)
    while heap:
        _, i, event, it = heap[0]
        yield event
        nxt = next(it, None)  # read the replacement only after yielding
        if nxt is None:
            heapq.heappop(heap)
        else:
            heapq.heapreplace(heap, (nxt["ts"], i, nxt, it))


# ── Part 3 ─────────────────────────────────────────────────────────


def deliver(events: Iterable[Event]) -> Iterator[Event]:
    pending: list[tuple[int, int, Event]] = []  # (due, arrival seq, event)
    for seq, event in enumerate(events):
        now = event["ts"]
        # Safe to release: nothing arriving later can be due before `now`.
        while pending and pending[0][0] <= now:
            yield heapq.heappop(pending)[2]
        due = max(now, event.get("deliver_at", now))
        heapq.heappush(pending, (due, seq, event))
    while pending:
        yield heapq.heappop(pending)[2]
