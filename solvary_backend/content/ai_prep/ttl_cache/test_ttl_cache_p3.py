# Provided tests for Part 3: capacity and LRU.

import pytest
import ttl_cache as tc


def fill(c, names, ttl=1000, now=0):
    for n in names:
        c.put(n, n.upper(), ttl=ttl, now=now)


def test_spec_example():
    c = tc.TTLCache(capacity=2)
    fill(c, ["a", "b"])
    c.get("a", 1)
    c.put("c", "C", ttl=100, now=2)
    assert c.keys(2) == ["a", "c"]
    assert c.get("b", 2) is None
    assert c.evictions() == 1


def test_non_positive_capacity_raises():
    for cap in [0, -1, -5]:
        with pytest.raises(ValueError):
            tc.TTLCache(capacity=cap)


def test_capacity_none_is_unbounded():
    c = tc.TTLCache()
    fill(c, [f"k{i}" for i in range(500)])
    assert c.size(0) == 500
    assert c.evictions() == 0


def test_evicts_least_recently_put_when_nothing_was_read():
    c = tc.TTLCache(capacity=3)
    fill(c, ["a", "b", "c"])
    c.put("d", "D", ttl=1000, now=1)
    assert c.keys(1) == ["b", "c", "d"]
    assert c.get("a", 1) is None


def test_get_refreshes_recency():
    c = tc.TTLCache(capacity=3)
    fill(c, ["a", "b", "c"])
    assert c.get("a", 1) == "A"
    assert c.keys(1) == ["b", "c", "a"]
    c.put("d", "D", ttl=1000, now=2)
    assert c.get("b", 2) is None
    assert c.get("a", 2) == "A"


def test_overwrite_moves_key_to_most_recent_and_never_evicts():
    c = tc.TTLCache(capacity=3)
    fill(c, ["a", "b", "c"])
    c.put("a", "A2", ttl=1000, now=1)
    assert c.evictions() == 0
    assert c.keys(1) == ["b", "c", "a"]
    assert c.get("a", 1) == "A2"


def test_overwrite_at_full_capacity_keeps_every_other_entry():
    c = tc.TTLCache(capacity=2)
    fill(c, ["a", "b"])
    c.put("b", "B2", ttl=5, now=1)
    assert c.size(1) == 2
    assert c.get("a", 1) == "A"


def test_expired_entries_are_removed_before_any_lru_eviction():
    c = tc.TTLCache(capacity=3)
    c.put("short", 1, ttl=5, now=0)
    c.put("b", 1, ttl=1000, now=0)
    c.put("c", 1, ttl=1000, now=0)
    c.put("d", 1, ttl=1000, now=10)
    assert c.evictions() == 0
    assert c.keys(10) == ["b", "c", "d"]


def test_expired_entry_that_was_read_often_is_still_removed():
    c = tc.TTLCache(capacity=2)
    c.put("hot", 1, ttl=5, now=0)
    c.put("cold", 1, ttl=1000, now=0)
    for t in range(5):
        assert c.get("hot", t) == 1
    c.put("new", 1, ttl=1000, now=5)
    assert c.get("hot", 5) is None
    assert c.keys(5) == ["cold", "new"]
    assert c.evictions() == 0


def test_never_read_entry_is_evicted_before_a_recently_read_one():
    c = tc.TTLCache(capacity=2)
    fill(c, ["old", "fresh"])
    c.get("old", 1)
    c.put("x", "X", ttl=1000, now=2)
    assert c.get("fresh", 2) is None
    assert c.get("old", 2) == "OLD"


def test_only_lru_evictions_are_counted():
    c = tc.TTLCache(capacity=2)
    c.put("a", 1, ttl=2, now=0)
    c.put("b", 1, ttl=1000, now=0)
    c.put("c", 1, ttl=1000, now=5)
    assert c.evictions() == 0
    c.put("d", 1, ttl=1000, now=6)
    assert c.evictions() == 1
    c.delete("d", 6)
    c.put("e", 1, ttl=1000, now=6)
    assert c.evictions() == 1


def test_delete_frees_a_slot_without_eviction():
    c = tc.TTLCache(capacity=2)
    fill(c, ["a", "b"])
    c.delete("a", 1)
    c.put("c", "C", ttl=1000, now=1)
    assert c.evictions() == 0
    assert c.keys(1) == ["b", "c"]


def test_expired_uncleaned_key_reput_is_a_new_entry_not_a_free_overwrite():
    c = tc.TTLCache(capacity=2)
    c.put("a", 1, ttl=5, now=0)
    c.put("b", 1, ttl=1000, now=0)
    c.put("a", 2, ttl=1000, now=10)
    assert c.evictions() == 0
    assert c.keys(10) == ["b", "a"]


def test_stale_heap_records_do_not_break_eviction_accounting():
    c = tc.TTLCache(capacity=2)
    for i in range(50):
        c.put("a", i + 1, ttl=10 + i, now=i)
    c.put("b", 1, ttl=1000, now=50)
    c.put("c", 1, ttl=1000, now=51)
    assert c.keys(51) == ["b", "c"]
    assert c.evictions() == 1
