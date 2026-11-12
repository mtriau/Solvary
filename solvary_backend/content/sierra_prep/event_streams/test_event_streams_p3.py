# Provided tests for Part 3: deferred delivery.

import random
from itertools import count, islice

import event_streams as es


def ev(ts, source="s", text=None, **extra):
    return {"ts": ts, "source": source, "text": text or f"{source}@{ts}", **extra}


class Counted:
    def __init__(self, events):
        self._it = iter(events)
        self.pulled = 0

    def __iter__(self):
        return self

    def __next__(self):
        event = next(self._it)
        self.pulled += 1
        return event


def test_spec_example():
    events = [
        ev(1, "customer", "where is my order?"),
        ev(2, "tool", "nudge", deliver_at=5),
        ev(3, "model", "checking..."),
        ev(4, "model", "it ships today"),
        ev(6, "customer", "thanks"),
    ]
    out = [e["text"] for e in es.deliver(events)]
    assert out == ["where is my order?", "checking...", "it ships today", "nudge", "thanks"]


def test_without_deferrals_the_order_is_unchanged():
    events = [ev(1), ev(1), ev(2), ev(5), ev(5), ev(9)]
    out = list(es.deliver(iter(events)))
    assert out == events
    assert all(a is b for a, b in zip(out, events))


def test_held_event_goes_before_an_arrival_due_at_the_same_time():
    events = [ev(1, "a", "held", deliver_at=4), ev(2, "b", "early"), ev(4, "c", "arrives at 4")]
    assert [e["text"] for e in es.deliver(events)] == ["early", "held", "arrives at 4"]


def test_two_deferred_events_due_together_keep_arrival_order():
    events = [ev(1, "a", "first", deliver_at=10), ev(2, "b", "second", deliver_at=10), ev(3, "c")]
    assert [e["text"] for e in es.deliver(events)] == ["c@3", "first", "second"]


def test_deliver_at_before_ts_means_ts():
    events = [ev(5, "a", "bad", deliver_at=1), ev(5, "b", "ok")]
    assert [e["text"] for e in es.deliver(events)] == ["bad", "ok"]


def test_releases_as_soon_as_safe_not_at_the_end():
    source = Counted([ev(ts) for ts in range(1, 1000)])
    out = es.deliver(source)
    assert source.pulled == 0
    taken = list(islice(out, 3))
    assert [e["ts"] for e in taken] == [1, 2, 3]
    assert source.pulled <= 4


def test_endless_input_with_deferrals():
    def feed():
        for ts in count(1):
            yield ev(ts, "t", deliver_at=ts + 2) if ts % 3 == 0 else ev(ts, "n")

    out = [e["ts"] for e in islice(es.deliver(feed()), 9)]
    # ts 3 is due at 5 and arrived before the event at 5, so it goes first;
    # likewise ts 6 (due 8) before 8.
    assert out == [1, 2, 4, 3, 5, 7, 6, 8, 10]


def test_composes_with_merge_live():
    a = iter([ev(1, "a"), ev(3, "a", deliver_at=8)])
    b = iter([ev(2, "b"), ev(5, "b"), ev(9, "b")])
    out = [(e["source"], e["ts"]) for e in es.deliver(es.merge_live([a, b]))]
    assert out == [("a", 1), ("b", 2), ("b", 5), ("a", 3), ("b", 9)]


def test_large_random_deferrals_match_a_stable_sort():
    rng = random.Random(7)
    events = []
    for ts in range(100_000):
        if rng.random() < 0.25:
            events.append(ev(ts, "d", deliver_at=ts + rng.randint(0, 500)))
        else:
            events.append(ev(ts, "n"))
    expected = sorted(events, key=lambda e: max(e["ts"], e.get("deliver_at", e["ts"])))
    out = list(es.deliver(iter(events)))
    assert out == expected
