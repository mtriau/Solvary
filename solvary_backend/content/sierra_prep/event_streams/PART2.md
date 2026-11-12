# Event Streams: Part 2

The sources are live now. Each stream is an **iterator** that may be very
long, slow, or endless, and the consumer wants events as they become
available, not after everything has finished.

### What to implement

`merge_live(streams: list[Iterable[Event]]) -> Iterator[Event]`

- Same ordering and tie rules as Part 1: by `ts`, ties by stream position,
  then original order.
- **Lazy.** Nothing is read from any stream until the consumer asks for the
  first event. The consumer may stop at any point (for example with
  `itertools.islice`), and streams may never end.
- **Bounded look-ahead.** To know which event is next you may hold **at most
  one unread event per stream**. Never read a second event from a stream
  while its first is still waiting to be yielded.
- A stream that runs out is simply dropped; the others continue.
- `merge_streams` from Part 1 must still work. It may become
  `list(merge_live(streams))`.

### Scale

Up to two thousand streams with a hundred events each. Picking the next event
by scanning every stream's head is too slow for the provided tests; use a
structure that gives you the smallest head in logarithmic time.

### Worked example

```python
from itertools import count, islice

def ticker(source, start, step):
    for ts in count(start, step):           # endless
        yield {"ts": ts, "source": source, "text": f"{source}@{ts}"}

live = merge_live([ticker("a", 0, 3), ticker("b", 1, 3), ticker("c", 2, 3)])
[e["ts"] for e in islice(live, 7)]          # -> [0, 1, 2, 3, 4, 5, 6]
```

### Clarifications

- **Does a generator function count as lazy?** Yes, that is the expected
  shape: `def merge_live(streams): ... yield event`.
- **What do I store in the heap?** Something that compares by `ts` first
  and never falls through to comparing the event dicts themselves (dicts
  do not support `<`). A tuple `(ts, stream_index, event, iterator)` works
  because `stream_index` is unique.
- **Does `heapq.merge` do this?** Yes, with `key=`, and it is fine to say
  so. Interviewers then ask you to write the loop yourself, so practise the
  loop.
- **Replacing versus pop and push:** `heapq.heapreplace` does both in one
  sift. Not required, but worth knowing.
- **Streams that are lists?** Still fine; `iter()` them.

Run the provided tests with **Submit**.

---
Interviewer notes

This is the heap part. Watch for three things: priming the heap with one
event per stream, a tuple layout that cannot fall through to comparing
dicts, and reading the replacement from a stream only after its head has
been yielded. A linear scan of stream heads is accepted by the small
tests and fails the 2000-stream test by time.
