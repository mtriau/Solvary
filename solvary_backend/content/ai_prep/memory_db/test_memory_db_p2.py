# Provided tests for Part 2: SCAN and SCAN_BY_PREFIX.

import memory_db


def make():
    return memory_db.MemoryDB()


def test_scan_formats_each_field_as_name_and_value_in_parentheses():
    db = make()
    db.set("k", "name", "Ada")
    assert db.scan("k") == ["name(Ada)"]


def test_scan_sorts_by_field_name_not_insertion_order():
    db = make()
    db.set("k", "zeta", "3")
    db.set("k", "alpha", "1")
    db.set("k", "mid", "2")
    assert db.scan("k") == ["alpha(1)", "mid(2)", "zeta(3)"]


def test_scan_unknown_key_is_empty_list():
    assert make().scan("nope") == []


def test_scan_only_lists_the_requested_record():
    db = make()
    db.set("k1", "a", "1")
    db.set("k2", "b", "2")
    assert db.scan("k1") == ["a(1)"]


def test_scan_reflects_overwrite_and_delete():
    db = make()
    db.set("k", "a", "1")
    db.set("k", "b", "2")
    db.set("k", "a", "9")
    db.delete("k", "b")
    assert db.scan("k") == ["a(9)"]


def test_scan_of_record_with_all_fields_deleted_is_empty():
    db = make()
    db.set("k", "a", "1")
    db.delete("k", "a")
    assert db.scan("k") == []
    assert db.scan_by_prefix("k", "") == []


def test_scan_sorting_is_plain_string_order_uppercase_before_lowercase():
    db = make()
    db.set("k", "b", "1")
    db.set("k", "B", "2")
    db.set("k", "a10", "3")
    db.set("k", "a2", "4")
    assert db.scan("k") == ["B(2)", "a10(3)", "a2(4)", "b(1)"]


def test_scan_by_prefix_keeps_only_matching_fields_sorted():
    db = make()
    for f, v in [("temp_max", "30"), ("name", "x"), ("temp_min", "10"), ("tem", "z")]:
        db.set("k", f, v)
    assert db.scan_by_prefix("k", "temp") == ["temp_max(30)", "temp_min(10)"]


def test_scan_by_prefix_matches_the_start_of_the_name_only():
    db = make()
    db.set("k", "xtemp", "1")
    db.set("k", "temp", "2")
    assert db.scan_by_prefix("k", "temp") == ["temp(2)"]


def test_scan_by_prefix_is_case_sensitive():
    db = make()
    db.set("k", "Name", "1")
    db.set("k", "name", "2")
    assert db.scan_by_prefix("k", "n") == ["name(2)"]


def test_scan_by_prefix_empty_prefix_matches_everything():
    db = make()
    db.set("k", "b", "2")
    db.set("k", "a", "1")
    assert db.scan_by_prefix("k", "") == db.scan("k") == ["a(1)", "b(2)"]


def test_scan_by_prefix_no_match_or_unknown_key_is_empty():
    db = make()
    db.set("k", "a", "1")
    assert db.scan_by_prefix("k", "zzz") == []
    assert db.scan_by_prefix("nope", "a") == []
