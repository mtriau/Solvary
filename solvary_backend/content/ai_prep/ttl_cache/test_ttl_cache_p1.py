# Provided tests for Part 1: put, get, delete with exact expiry.

import pytest
import ttl_cache as tc


def test_spec_example():
    c = tc.TTLCache()
    c.put("a", 1, ttl=10, now=0)
    assert c.get("a", 0) == 1
    assert c.get("a", 9) == 1
    assert c.get("a", 10) is None
    assert c.size(10) == 0


def test_alive_one_tick_before_expiry_gone_exactly_at_expiry():
    c = tc.TTLCache()
    c.put("k", "v", ttl=100, now=50)
    assert c.get("k", 149) == "v"
    assert c.get("k", 150) is None


def test_entry_alive_at_its_own_put_time():
    c = tc.TTLCache()
    c.put("k", "v", ttl=1, now=7)
    assert c.get("k", 7) == "v"
    assert c.get("k", 8) is None


def test_overwrite_replaces_value():
    c = tc.TTLCache()
    c.put("k", "old", ttl=10, now=0)
    c.put("k", "new", ttl=10, now=1)
    assert c.get("k", 2) == "new"
    assert c.size(2) == 1


def test_overwrite_with_shorter_ttl_forgets_the_longer_expiry():
    c = tc.TTLCache()
    c.put("k", "a", ttl=100, now=0)
    c.put("k", "b", ttl=5, now=10)
    assert c.get("k", 14) == "b"
    assert c.get("k", 15) is None


def test_overwrite_with_longer_ttl_forgets_the_shorter_expiry():
    c = tc.TTLCache()
    c.put("k", "a", ttl=5, now=0)
    c.put("k", "b", ttl=50, now=3)
    assert c.get("k", 5) == "b"
    assert c.get("k", 52) == "b"
    assert c.get("k", 53) is None


def test_overwrite_after_expiry_revives_the_key():
    c = tc.TTLCache()
    c.put("k", "a", ttl=5, now=0)
    c.put("k", "b", ttl=5, now=20)
    assert c.get("k", 24) == "b"


def test_delete_live_entry_returns_true_and_removes_it():
    c = tc.TTLCache()
    c.put("k", 1, ttl=10, now=0)
    assert c.delete("k", 3) is True
    assert c.get("k", 3) is None
    assert c.delete("k", 3) is False


def test_delete_expired_entry_returns_false():
    c = tc.TTLCache()
    c.put("k", 1, ttl=10, now=0)
    assert c.delete("k", 10) is False
    assert c.size(10) == 0


def test_delete_missing_key_returns_false():
    assert tc.TTLCache().delete("ghost", 0) is False


def test_size_counts_only_live_entries():
    c = tc.TTLCache()
    c.put("a", 1, ttl=5, now=0)
    c.put("b", 1, ttl=10, now=0)
    c.put("c", 1, ttl=15, now=0)
    assert c.size(0) == 3
    assert c.size(5) == 2
    assert c.size(10) == 1
    assert c.size(15) == 0


def test_non_positive_ttl_raises():
    for ttl in [0, -1, -100]:
        c = tc.TTLCache()
        with pytest.raises(ValueError):
            c.put("k", 1, ttl=ttl, now=0)
        assert c.size(0) == 0


def test_none_value_is_rejected_so_get_none_means_absent():
    c = tc.TTLCache()
    with pytest.raises(ValueError):
        c.put("k", None, ttl=5, now=0)
    assert c.get("k", 0) is None
    assert c.size(0) == 0


def test_falsy_values_other_than_none_are_stored():
    c = tc.TTLCache()
    for key, value in [("zero", 0), ("empty", ""), ("no", False), ("list", [])]:
        c.put(key, value, ttl=5, now=0)
    assert c.get("zero", 1) == 0
    assert c.get("empty", 1) == ""
    assert c.get("no", 1) is False
    assert c.get("list", 1) == []
