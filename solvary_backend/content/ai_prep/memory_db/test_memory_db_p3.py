# Provided tests for Part 3: timestamps and TTL.

import memory_db


def make():
    return memory_db.MemoryDB()


def test_plain_set_at_never_expires():
    db = make()
    db.set_at("k", "f", "v", 1)
    assert db.get_at("k", "f", 10**9) == "v"


def test_ttl_field_is_present_one_tick_before_expiry():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 10, 5)
    assert db.get_at("k", "f", 14) == "v"


def test_ttl_field_is_gone_exactly_at_timestamp_plus_ttl():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 10, 5)
    assert db.get_at("k", "f", 15) is None


def test_overwrite_before_expiry_replaces_the_ttl_with_the_new_one():
    db = make()
    db.set_at_with_ttl("k", "f", "old", 1, 10)   # would expire at 11
    db.set_at_with_ttl("k", "f", "new", 5, 100)  # now expires at 105
    assert db.get_at("k", "f", 50) == "new"
    assert db.get_at("k", "f", 104) == "new"
    assert db.get_at("k", "f", 105) is None


def test_overwrite_with_shorter_ttl_expires_sooner():
    db = make()
    db.set_at_with_ttl("k", "f", "old", 1, 100)
    db.set_at_with_ttl("k", "f", "new", 2, 3)
    assert db.get_at("k", "f", 4) == "new"
    assert db.get_at("k", "f", 5) is None


def test_plain_set_at_after_ttl_set_makes_the_field_permanent():
    db = make()
    db.set_at_with_ttl("k", "f", "v1", 1, 5)
    db.set_at("k", "f", "v2", 3)
    assert db.get_at("k", "f", 6) == "v2"
    assert db.get_at("k", "f", 10**6) == "v2"


def test_delete_at_live_field_returns_true_and_removes_it():
    db = make()
    db.set_at("k", "f", "v", 1)
    assert db.delete_at("k", "f", 2) is True
    assert db.get_at("k", "f", 3) is None


def test_delete_at_missing_field_returns_false():
    db = make()
    db.set_at("k", "f", "v", 1)
    assert db.delete_at("k", "other", 2) is False
    assert db.delete_at("nope", "f", 3) is False


def test_delete_at_expired_field_returns_false():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 1, 5)
    assert db.delete_at("k", "f", 6) is False


def test_delete_at_on_last_tick_of_ttl_still_deletes():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 1, 5)
    assert db.delete_at("k", "f", 5) is True


def test_delete_then_set_again_does_not_inherit_the_old_ttl():
    db = make()
    db.set_at_with_ttl("k", "f", "v1", 1, 5)
    assert db.delete_at("k", "f", 2) is True
    db.set_at("k", "f", "v2", 3)
    assert db.get_at("k", "f", 100) == "v2"


def test_scan_at_excludes_expired_fields_and_keeps_sorted_order():
    db = make()
    db.set_at_with_ttl("k", "b", "2", 1, 10)  # alive until 11
    db.set_at_with_ttl("k", "a", "1", 2, 3)   # alive until 5
    db.set_at("k", "c", "3", 3)
    assert db.scan_at("k", 4) == ["a(1)", "b(2)", "c(3)"]
    assert db.scan_at("k", 5) == ["b(2)", "c(3)"]
    assert db.scan_at("k", 11) == ["c(3)"]


def test_scan_by_prefix_at_filters_by_prefix_and_expiry():
    db = make()
    db.set_at_with_ttl("k", "tmp_a", "1", 1, 5)
    db.set_at("k", "tmp_b", "2", 2)
    db.set_at("k", "other", "3", 3)
    assert db.scan_by_prefix_at("k", "tmp", 5) == ["tmp_a(1)", "tmp_b(2)"]
    assert db.scan_by_prefix_at("k", "tmp", 6) == ["tmp_b(2)"]


def test_plain_methods_still_work_without_any_timestamps():
    db = make()
    db.set("k", "b", "2")
    db.set("k", "a", "1")
    assert db.get("k", "a") == "1"
    assert db.scan("k") == ["a(1)", "b(2)"]
    assert db.delete("k", "a") is True
    assert db.scan_by_prefix("k", "") == ["b(2)"]


def test_plain_methods_run_at_the_latest_timestamp_seen_so_far():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 10, 5)
    db.set_at("k", "g", "w", 14)
    assert db.get("k", "f") == "v"        # latest timestamp is 14 < 15
    db.set_at("k", "h", "x", 15)
    assert db.get("k", "f") is None       # latest timestamp is now 15
    assert db.scan("k") == ["g(w)", "h(x)"]
