# Event Streams: Part 3

Some events should not surface when they happen. A tool can schedule a
follow-up ("remind the customer in 10 minutes"), and the model can hold a
message until a tool has had time to finish. Such events carry a delivery
time, and the timeline the customer sees must be in **delivery order**.

### What to implement

`deliver(events: Iterable[Event]) -> Iterator[Event]`

- The input is a stream of events already in `ts` order, typically
  `merge_live(...)`. Treat it as live: long or endless, consumed lazily.
- An event's **due time** is `event["deliver_at"]` if that key is present,
  otherwise `event["ts"]`. `deliver_at` is never earlier than `ts`; if it
  somehow is, use `ts`.
- Yield the events in order of due time.
- **Ties:** two events due at the same time come out in the order they
  arrived in the input.
- **Yield as early as it is safe.** As soon as you know that no later
  input event can be due before a held event, let it go. Do not wait for
  the input to end. (Why it is safe: every future input event has
  `ts >= the current ts`, and its due time is at least its `ts`.)
- When the input ends, release whatever is still held, in due order.

### Worked example

```python
events = [
    {"ts": 1, "source": "customer", "text": "where is my order?"},
    {"ts": 2, "source": "tool", "text": "nudge", "deliver_at": 5},
    {"ts": 3, "source": "model", "text": "checking..."},
    {"ts": 4, "source": "model", "text": "it ships today"},
    {"ts": 6, "source": "customer", "text": "thanks"},
]
[e["text"] for e in deliver(events)]
# -> ["where is my order?", "checking...", "it ships today", "nudge", "thanks"]
```

### Clarifications

- **How far ahead may I read?** One event. After yielding `k` events you
  may have read at most `k + 1` from the input, in the common case where
  nothing is deferred.
- **A held event due at exactly the `ts` of the next input event?** The
  held one goes first: it arrived earlier.
- **Does `merge_live` change?** No. `deliver(merge_live(streams))` is the
  intended composition. Two heaps, one per function.
- **Memory:** at most as many held events as are simultaneously deferred.
- **Scale:** a hundred thousand events, a quarter of them deferred by a
  random amount.

Run the provided tests with **Submit**.

---
Interviewer notes

A second heap keyed by `(due, arrival_seq, event)`. The reasoning to hear
out loud: an event can be released once the input's current `ts` has
reached its due time, because no later input can be due before that. The
common slip is flushing only at the end (fails the look-ahead test) or
flushing with `<` instead of `<=` (fails the tie test).
