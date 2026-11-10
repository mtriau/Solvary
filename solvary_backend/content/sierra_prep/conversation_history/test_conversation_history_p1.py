# Provided tests for Part 1: fetch_all over a paginated, flaky conversation API.

import pytest
from conversation_history import Message, PaginationError, TransientError, fetch_all


def msg(i: int) -> Message:
    return Message(id=f"m{i}", role="user", text=f"text {i}", tokens=1)


class FakeAPI:
    """pages: cursor -> (messages, next_cursor); failures: cursor -> how many
    TransientErrors to raise before succeeding."""

    def __init__(self, pages, failures=None):
        self.pages = pages
        self.failures = dict(failures or {})
        self.calls: list = []

    def fetch_page(self, cursor):
        self.calls.append(cursor)
        if self.failures.get(cursor, 0) > 0:
            self.failures[cursor] -= 1
            raise TransientError(f"flaky at {cursor!r}")
        return self.pages[cursor]


def test_single_page():
    api = FakeAPI({None: ([msg(1), msg(2)], None)})
    assert fetch_all(api.fetch_page) == [msg(1), msg(2)]
    assert api.calls == [None]


def test_three_pages_in_order():
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([msg(2), msg(3)], "b"), "b": ([msg(4)], None)})
    assert fetch_all(api.fetch_page) == [msg(1), msg(2), msg(3), msg(4)]
    assert api.calls == [None, "a", "b"]


def test_empty_conversation():
    api = FakeAPI({None: ([], None)})
    assert fetch_all(api.fetch_page) == []


def test_empty_middle_page_with_next_cursor_continues():
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([], "b"), "b": ([msg(2)], None)})
    assert fetch_all(api.fetch_page) == [msg(1), msg(2)]


def test_no_extra_calls_on_happy_path():
    pages = {None: ([msg(1)], "a"), "a": ([msg(2)], None)}
    api = FakeAPI(pages)
    fetch_all(api.fetch_page)
    assert len(api.calls) == 2


def test_transient_error_is_retried_on_the_same_cursor():
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([msg(2)], None)}, failures={"a": 2})
    assert fetch_all(api.fetch_page) == [msg(1), msg(2)]
    assert api.calls == [None, "a", "a", "a"]


def test_retry_never_duplicates_or_loses_messages():
    api = FakeAPI(
        {None: ([msg(1)], "a"), "a": ([msg(2)], "b"), "b": ([msg(3)], None)},
        failures={None: 1, "a": 1, "b": 1},
    )
    assert fetch_all(api.fetch_page) == [msg(1), msg(2), msg(3)]


def test_max_retries_is_per_cursor_and_counts_retries_not_calls():
    # 3 failures then success on each cursor: 4 calls each, allowed with max_retries=3
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([msg(2)], None)}, failures={None: 3, "a": 3})
    assert fetch_all(api.fetch_page, max_retries=3) == [msg(1), msg(2)]
    assert api.calls.count(None) == 4 and api.calls.count("a") == 4


def test_exhausted_retries_propagate_the_transient_error():
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([msg(2)], None)}, failures={"a": 3})
    with pytest.raises(TransientError):
        fetch_all(api.fetch_page, max_retries=2)
    assert api.calls == [None, "a", "a", "a"]


def test_zero_retries_means_one_attempt():
    api = FakeAPI({None: ([msg(1)], None)}, failures={None: 1})
    with pytest.raises(TransientError):
        fetch_all(api.fetch_page, max_retries=0)
    assert api.calls == [None]


def test_repeated_cursor_raises_pagination_error():
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([msg(2)], "a")})
    with pytest.raises(PaginationError):
        fetch_all(api.fetch_page)
    assert len(api.calls) <= 3


def test_cursor_that_points_back_to_the_start_raises():
    # the API returns None again as "next" … but None was the first cursor.
    api = FakeAPI({None: ([msg(1)], "a"), "a": ([msg(2)], "b"), "b": ([msg(3)], "a")})
    with pytest.raises(PaginationError):
        fetch_all(api.fetch_page)


def test_many_pages():
    pages = {}
    for i in range(500):
        cur = None if i == 0 else f"c{i}"
        nxt = None if i == 499 else f"c{i + 1}"
        pages[cur] = ([msg(i)], nxt)
    api = FakeAPI(pages)
    out = fetch_all(api.fetch_page)
    assert [m.id for m in out] == [f"m{i}" for i in range(500)]
    assert len(api.calls) == 500
