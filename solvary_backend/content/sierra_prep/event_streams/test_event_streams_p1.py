# Provided tests for Part 1: merge time-ordered event lists.

import event_streams as es


def ev(ts, source="s", text=None, **extra):
    return {"ts": ts, "source": source, "text": text or f"{source}@{ts}", **extra}


def test_spec_example():
    model = [ev(1, "model", "thinking"), ev(4, "model", "reply")]
    tool = [ev(2, "search", "query"), ev(4, "search", "3 results")]
    chat = [ev(3, "customer", "hello?")]
    out = es.merge_streams([model, tool, chat])
    assert [e["text"] for e in out] == ["thinking", "query", "hello?", "reply", "3 results"]


def test_no_streams_and_empty_streams():
    assert es.merge_streams([]) == []
    assert es.merge_streams([[], []]) == []
    only = [ev(1), ev(2)]
    assert es.merge_streams([[], only, []]) == only


def test_single_stream_is_unchanged():
    stream = [ev(1), ev(1), ev(5), ev(9)]
    assert es.merge_streams([stream]) == stream


def test_events_are_the_same_objects_not_copies():
    a, b = ev(1, "a"), ev(2, "b", extra="kept")
    out = es.merge_streams([[b], [a]])
    assert out[0] is a and out[1] is b
    assert out[1]["extra"] == "kept"


def test_ties_keep_stream_order_then_original_order():
    first = [ev(5, "first", "f1"), ev(5, "first", "f2")]
    second = [ev(5, "second", "s1")]
    third = [ev(5, "third", "t1"), ev(5, "third", "t2")]
    out = es.merge_streams([first, second, third])
    assert [e["text"] for e in out] == ["f1", "f2", "s1", "t1", "t2"]


def test_inputs_are_not_modified():
    a = [ev(1), ev(3)]
    b = [ev(2), ev(4)]
    snapshot = ([dict(e) for e in a], [dict(e) for e in b])
    es.merge_streams([a, b])
    assert (a, b) == snapshot
    assert len(a) == 2 and len(b) == 2


def test_many_streams_interleave_correctly():
    streams = [[ev(j * 7 + i) for j in range(50)] for i in range(7)]
    out = es.merge_streams(streams)
    assert [e["ts"] for e in out] == list(range(350))
