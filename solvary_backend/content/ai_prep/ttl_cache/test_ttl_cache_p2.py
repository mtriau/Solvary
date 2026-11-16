# Provided tests for Part 2: cleanup without scanning.

import time

import ttl_cache as tc


def test_cleanup_removes_expired_and_returns_count():
    c = tc.TTLCache()
    for i, ttl in enumerate([5, 10, 15, 20]):
        c.put(f"k{i}", i + 1, ttl=ttl, now=0)
    assert c.cleanup(10) == 2
    assert c.size(10) == 2
    assert c.get("k2", 10) == 3


def test_cleanup_with_nothing_expired_returns_zero():
    c = tc.TTLCache()
    c.put("a", 1, ttl=10, now=0)
    assert c.cleanup(5) == 0
    assert c.cleanup(9) == 0
    assert c.get("a", 9) == 1


def test_cleanup_boundary_is_half_open():
    c = tc.TTLCache()
    c.put("a", 1, ttl=10, now=0)
    assert c.cleanup(9) == 0
    assert c.cleanup(10) == 1


def test_stale_record_of_overwritten_key_does_not_remove_the_live_entry():
    c = tc.TTLCache()
    c.put("k", "a", ttl=5, now=0)
    c.put("k", "b", ttl=50, now=1)
    assert c.cleanup(5) == 0
    assert c.get("k", 5) == "b"
    assert c.cleanup(20) == 0
    assert c.size(20) == 1


def test_overwritten_key_is_counted_once_at_its_real_expiry():
    c = tc.TTLCache()
    c.put("k", "a", ttl=5, now=0)
    c.put("k", "b", ttl=20, now=1)
    assert c.cleanup(100) == 1


def test_deleted_key_is_not_counted_by_cleanup():
    c = tc.TTLCache()
    c.put("a", 1, ttl=5, now=0)
    c.put("b", 1, ttl=5, now=0)
    assert c.delete("a", 1) is True
    assert c.cleanup(5) == 1


def test_delete_then_reput_keeps_the_new_entry():
    c = tc.TTLCache()
    c.put("k", "old", ttl=5, now=0)
    c.delete("k", 1)
    c.put("k", "new", ttl=100, now=2)
    assert c.cleanup(5) == 0
    assert c.get("k", 5) == "new"


def test_entry_removed_by_get_is_not_counted_again_by_cleanup():
    c = tc.TTLCache()
    c.put("k", 1, ttl=5, now=0)
    assert c.get("k", 5) is None
    assert c.cleanup(5) == 0


def test_shortened_ttl_is_honoured_by_cleanup():
    c = tc.TTLCache()
    c.put("k", "a", ttl=100, now=0)
    c.put("k", "b", ttl=5, now=1)
    assert c.cleanup(6) == 1
    assert c.size(6) == 0


def test_expiring_before_orders_by_expiry_then_key():
    c = tc.TTLCache()
    c.put("b", 1, ttl=10, now=0)
    c.put("a", 1, ttl=10, now=0)
    c.put("z", 1, ttl=3, now=0)
    c.put("late", 1, ttl=50, now=0)
    assert c.expiring_before(11, 0) == ["z", "a", "b"]
    assert c.expiring_before(10, 0) == ["z"]
    assert c.expiring_before(1000, 0) == ["z", "a", "b", "late"]


def test_expiring_before_skips_stale_records_and_expired_entries():
    c = tc.TTLCache()
    c.put("a", 1, ttl=5, now=0)
    c.put("a", 1, ttl=50, now=1)
    c.put("gone", 1, ttl=5, now=0)
    c.delete("gone", 1)
    c.put("old", 1, ttl=2, now=0)
    c.put("b", 1, ttl=20, now=0)
    assert c.expiring_before(30, 3) == ["b"]
    assert c.expiring_before(60, 3) == ["b", "a"]


def test_many_expiries_in_one_tick_all_go_in_one_cleanup():
    c = tc.TTLCache()
    for i in range(1000):
        c.put(f"k{i}", i + 1, ttl=10, now=0)
    assert c.size(9) == 1000
    assert c.cleanup(10) == 1000
    assert c.size(10) == 0


def test_performance_cleanup_does_not_scan_the_whole_cache():
    c = tc.TTLCache()
    n = 200_000
    for i in range(n):
        c.put(f"k{i}", i + 1, ttl=i + 1, now=0)
    start = time.perf_counter()
    removed = 0
    for step in range(1, 1001):
        removed += c.cleanup(step * 200)
    elapsed = time.perf_counter() - start
    assert removed == n
    assert elapsed < 1.5, f"cleanup took {elapsed:.2f}s; it looks like a full scan per call"


def test_performance_stale_records_never_remove_live_entries():
    c = tc.TTLCache()
    for i in range(100_000):
        c.put(f"k{i % 10}", i, ttl=i + 1, now=0)
    start = time.perf_counter()
    assert c.cleanup(50_000) == 0
    assert c.cleanup(99_000) == 0
    elapsed = time.perf_counter() - start
    assert c.size(99_000) == 10
    assert c.get("k9", 99_000) == 99_999
    assert elapsed < 1.5
