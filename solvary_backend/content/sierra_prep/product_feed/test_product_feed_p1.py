# Provided tests for Part 1: fetch_products over a flaky, paginated API.

import pytest
from product_feed import TransientError, fetch_products


class FakeAPI:
    """pages: cursor -> (items, next_cursor); failures: cursor -> number of
    TransientErrors to raise before that page succeeds."""

    def __init__(self, pages, failures=None):
        self.pages = pages
        self.failures = dict(failures or {})
        self.calls: list = []

    def list_products(self, cursor=None):
        self.calls.append(cursor)
        if self.failures.get(cursor, 0) > 0:
            self.failures[cursor] -= 1
            raise TransientError(f"503 at {cursor!r}")
        items, nxt = self.pages[cursor]
        return {"items": items, "next_cursor": nxt}


def item(i):
    return {"product_id": f"p{i}", "n": i}


def test_single_page():
    api = FakeAPI({None: ([item(1), item(2)], None)})
    assert fetch_products(api) == [item(1), item(2)]
    assert api.calls == [None]


def test_pages_are_concatenated_in_order():
    api = FakeAPI({None: ([item(1)], "p2"), "p2": ([item(2), item(3)], "p3"), "p3": ([item(4)], None)})
    assert fetch_products(api) == [item(1), item(2), item(3), item(4)]
    assert api.calls == [None, "p2", "p3"]


def test_empty_feed():
    api = FakeAPI({None: ([], None)})
    assert fetch_products(api) == []


def test_empty_page_with_cursor_continues():
    api = FakeAPI({None: ([], "p2"), "p2": ([item(1)], None)})
    assert fetch_products(api) == [item(1)]


def test_items_are_the_same_objects_not_copies():
    a = item(1)
    api = FakeAPI({None: ([a], None)})
    assert fetch_products(api)[0] is a


def test_spec_example_one_failure_then_success():
    api = FakeAPI({None: ([item(1), item(2)], "p2"), "p2": ([item(3)], None)}, failures={"p2": 1})
    assert fetch_products(api) == [item(1), item(2), item(3)]
    assert api.calls == [None, "p2", "p2"]


def test_retry_does_not_duplicate_items():
    api = FakeAPI({None: ([item(1)], "p2"), "p2": ([item(2)], None)}, failures={None: 2, "p2": 2})
    assert fetch_products(api) == [item(1), item(2)]


def test_max_attempts_counts_total_calls_per_page():
    api = FakeAPI({None: ([item(1)], None)}, failures={None: 4})
    assert fetch_products(api, max_attempts=5) == [item(1)]
    assert api.calls == [None] * 5


def test_exhausted_attempts_propagate():
    api = FakeAPI({None: ([item(1)], "p2"), "p2": ([item(2)], None)}, failures={"p2": 3})
    with pytest.raises(TransientError):
        fetch_products(api, max_attempts=3)
    assert api.calls == [None, "p2", "p2", "p2"]


def test_single_attempt_means_no_retry():
    api = FakeAPI({None: ([item(1)], None)}, failures={None: 1})
    with pytest.raises(TransientError):
        fetch_products(api, max_attempts=1)
    assert api.calls == [None]


def test_other_exceptions_are_not_retried():
    class Boom(Exception):
        pass

    class BadAPI:
        def __init__(self):
            self.calls = 0

        def list_products(self, cursor=None):
            self.calls += 1
            raise Boom()

    api = BadAPI()
    with pytest.raises(Boom):
        fetch_products(api)
    assert api.calls == 1
