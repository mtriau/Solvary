# Provided tests for Part 2: lazy merge over live iterators.

from itertools import count, islice

import event_streams as es


def ev(ts, source="s", text=None, **extra):
    return {"ts": ts, "source": source, "text": text or f"{source}@{ts}", **extra}


class Counted:
    """An iterator that counts how many events were read from it."""

    def __init__(self, events):
        self._it = iter(events)
        self.pulled = 0

    def __iter__(self):
        return self

    def __next__(self):
        event = next(self._it)
        self.pulled += 1
        return event


def ticker(source, start, step):
    for ts in count(start, step):
        yield ev(ts, source)


def test_spec_example_endless_streams():
    live = es.merge_live([ticker("a", 0, 3), ticker("b", 1, 3), ticker("c", 2, 3)])
    assert [e["ts"] for e in islice(live, 7)] == [0, 1, 2, 3, 4, 5, 6]


def test_nothing_is_read_before_the_consumer_asks():
    a, b = Counted([ev(1), ev(3)]), Counted([ev(2)])
    live = es.merge_live([a, b])
    assert (a.pulled, b.pulled) == (0, 0)
    assert next(live)["ts"] == 1
    assert a.pulled >= 1


def test_at_most_one_unread_event_per_stream():
    a = Counted([ev(ts, "a") for ts in range(1, 200, 2)])
    b = Counted([ev(ts, "b") for ts in range(2, 200, 2)])
    live = es.merge_live([a, b])
    taken = list(islice(live, 50))
    assert [e["ts"] for e in taken] == list(range(1, 51))
    from_a = sum(e["source"] == "a" for e in taken)
    from_b = len(taken) - from_a
    assert a.pulled <= from_a + 1
    assert b.pulled <= from_b + 1


def test_ties_follow_stream_position_then_original_order():
    live = es.merge_live([iter([ev(5, "x", "x1"), ev(5, "x", "x2")]), iter([ev(5, "y", "y1")])])
    assert [e["text"] for e in live] == ["x1", "x2", "y1"]


def test_exhausted_stream_is_dropped_and_others_continue():
    short = iter([ev(1), ev(2)])
    long = iter([ev(0), ev(3), ev(4), ev(5)])
    assert [e["ts"] for e in es.merge_live([short, long])] == [0, 1, 2, 3, 4, 5]


def test_empty_inputs():
    assert list(es.merge_live([])) == []
    assert list(es.merge_live([iter([]), iter([])])) == []
    assert [e["ts"] for e in es.merge_live([iter([]), iter([ev(7)])])] == [7]


def test_lists_are_accepted_as_streams_and_part1_still_works():
    a, b = [ev(1), ev(4)], [ev(2), ev(3)]
    assert [e["ts"] for e in es.merge_live([a, b])] == [1, 2, 3, 4]
    assert [e["ts"] for e in es.merge_streams([a, b])] == [1, 2, 3, 4]


def test_two_thousand_streams_need_logarithmic_selection():
    n_streams, per_stream = 2000, 100
    streams = [
        iter([ev(j * n_streams + i, str(i)) for j in range(per_stream)]) for i in range(n_streams)
    ]
    merged = es.merge_live(streams)
    assert all(e["ts"] == k for k, e in enumerate(merged))
