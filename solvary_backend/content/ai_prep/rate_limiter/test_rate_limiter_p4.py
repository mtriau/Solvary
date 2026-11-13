# Provided tests for Part 4: compound rules and a shared store.

import math
import pickle
from collections.abc import MutableMapping

import pytest

import rate_limiter as rl

TIERS = {"pro": (10, 0.0), "free": (10, 0.0)}
SEARCH = "url:/search"


def make():
    limiter = rl.RateLimiter(TIERS)
    limiter.set_client_tier("a", "pro")
    limiter.add_rule("pro", SEARCH, 2, 0.0)
    return limiter


def count(limiter, now=0.0, n=50, **kw):
    return sum(limiter.allow("a", now, **kw) for _ in range(n))


def test_a_scope_rule_limits_that_scope_but_not_other_traffic():
    limiter = make()
    assert count(limiter, scope=SEARCH) == 2
    assert limiter.allow("a", 0.0, scope=SEARCH) is False
    assert limiter.allow("a", 0.0) is True  # plain traffic still has base tokens


def test_scope_without_a_rule_only_uses_the_base_bucket():
    limiter = make()
    assert count(limiter, scope="url:/other") == 10


def test_rejection_by_the_scope_bucket_consumes_nothing():
    limiter = make()
    assert count(limiter, scope=SEARCH) == 2
    assert limiter.tokens("a", 0.0) == pytest.approx(8.0)
    assert limiter.allow("a", 0.0, scope=SEARCH) is False
    assert limiter.tokens("a", 0.0) == pytest.approx(8.0)


def test_rejection_by_the_base_bucket_leaves_the_scope_bucket_untouched():
    limiter = rl.RateLimiter({"t": (3, 1.0)})
    limiter.set_client_tier("a", "t")
    limiter.add_rule("t", SEARCH, 5, 1.0)
    assert count(limiter, n=3) == 3  # base is empty
    assert limiter.allow("a", 0.0, scope=SEARCH) is False
    assert limiter.tokens("a", 0.0, scope=SEARCH) == pytest.approx(5.0)
    assert limiter.allow("a", 1.0, scope=SEARCH) is True  # one base token, 5 scope tokens


def test_payload_cost_consumes_that_many_tokens_from_each_bucket():
    limiter = rl.RateLimiter({"t": (100, 0.0)})
    limiter.set_client_tier("a", "t")
    limiter.add_rule("t", "payload", 50, 0.0)
    assert limiter.allow("a", 0.0, scope="payload", cost=30) is True
    assert limiter.allow("a", 0.0, scope="payload", cost=30) is False  # 20 left
    assert limiter.allow("a", 0.0, scope="payload", cost=20) is True
    assert limiter.tokens("a", 0.0) == pytest.approx(50.0)
    assert limiter.tokens("a", 0.0, scope="payload") == pytest.approx(0.0)


def test_cost_larger_than_capacity_is_always_denied_and_consumes_nothing():
    limiter = rl.RateLimiter({"t": (100, 50.0)})
    limiter.set_client_tier("a", "t")
    limiter.add_rule("t", "payload", 50, 50.0)
    assert limiter.allow("a", 0.0, scope="payload", cost=51) is False  # base would pass
    assert limiter.allow("a", 1e9, scope="payload", cost=51) is False  # even after any idle
    assert limiter.allow("a", 1e9, cost=101) is False
    assert limiter.tokens("a", 1e9) == pytest.approx(100.0)
    assert math.isinf(limiter.retry_after("a", 1e9, scope="payload", cost=51))


def test_cost_must_be_positive():
    limiter = make()
    for bad in (0, -1):
        with pytest.raises(ValueError):
            limiter.allow("a", 0.0, cost=bad)


def test_rules_are_per_client_and_per_tier():
    limiter = make()
    limiter.set_client_tier("b", "pro")
    limiter.set_client_tier("f", "free")  # no rule for SEARCH in this tier
    assert count(limiter, scope=SEARCH) == 2
    assert limiter.allow("b", 0.0, scope=SEARCH) is True
    assert sum(limiter.allow("f", 0.0, scope=SEARCH) for _ in range(50)) == 10


def test_retry_after_is_the_slowest_bucket():
    limiter = rl.RateLimiter({"t": (10, 10.0)})
    limiter.set_client_tier("a", "t")
    limiter.add_rule("t", SEARCH, 2, 0.5)
    assert count(limiter, scope=SEARCH) == 2
    assert limiter.retry_after("a", 0.0, scope=SEARCH) == pytest.approx(2.0)
    assert limiter.retry_after("a", 0.0) == 0.0
    assert limiter.retry_after("a", 0.0, scope=SEARCH, cost=2) == pytest.approx(4.0)


def two_nodes(store, tiers=None):
    nodes = []
    for _ in range(2):
        node = rl.RateLimiter(tiers or {"t": (5, 0.0)}, store=store)
        node.set_client_tier("a", "t")
        nodes.append(node)
    return nodes


def test_two_nodes_over_one_store_share_the_budget():
    n1, n2 = two_nodes({})
    allowed = sum(node.allow("a", 0.0) for _ in range(10) for node in (n1, n2))
    assert allowed == 5


def test_refill_is_shared_across_nodes():
    n1, n2 = two_nodes({}, {"t": (2, 1.0)})
    assert n1.allow("a", 0.0) and n2.allow("a", 0.0)
    assert not n1.allow("a", 0.0) and not n2.allow("a", 0.0)
    assert n2.allow("a", 1.0) is True  # one token accrued, whichever node asks
    assert n1.allow("a", 1.0) is False


class PickledStore(MutableMapping):
    """A store that keeps serialized copies, like Redis would: mutating an
    object you read does nothing until you write it back."""

    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        return pickle.loads(self._data[key])

    def __setitem__(self, key, value):
        self._data[key] = pickle.dumps(value)

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


def test_works_with_any_mutable_mapping_that_copies_values():
    n1, n2 = two_nodes(PickledStore())
    allowed = sum(node.allow("a", 0.0) for _ in range(10) for node in (n1, n2))
    assert allowed == 5


def test_nodes_share_scope_and_payload_budgets_too():
    store = {}
    nodes = []
    for _ in range(2):
        node = rl.RateLimiter({"t": (100, 0.0)}, store=store)
        node.set_client_tier("a", "t")
        node.add_rule("t", "payload", 50, 0.0)
        nodes.append(node)
    n1, n2 = nodes
    assert n1.allow("a", 0.0, scope="payload", cost=30) is True
    assert n2.allow("a", 0.0, scope="payload", cost=30) is False
    assert n2.allow("a", 0.0, scope="payload", cost=20) is True
    assert n1.tokens("a", 0.0) == pytest.approx(50.0)
