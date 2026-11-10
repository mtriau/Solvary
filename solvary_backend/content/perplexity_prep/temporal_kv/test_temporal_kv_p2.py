# Provided tests for Part 2: delete (tombstone) and get_range.
# Run with: pytest temporal_kv -q

from temporal_kv import TemporalKV


def _spec_kv() -> TemporalKV:
    kv = TemporalKV()
    kv.set("a", "v", 1)
    kv.delete("a", 5)
    kv.set("a", "w", 9)
    return kv


def test_delete_makes_get_none_from_ts_onward():
    kv = _spec_kv()
    assert kv.get("a", 5) is None
    assert kv.get("a", 8) is None


def test_get_before_delete_still_sees_value():
    kv = _spec_kv()
    assert kv.get("a", 4) == "v"
    assert kv.get("a", 1) == "v"


def test_set_after_delete_restores_a_value():
    kv = _spec_kv()
    assert kv.get("a", 9) == "w"
    assert kv.get("a", 100) == "w"


def test_delete_with_no_later_set_stays_none_forever():
    kv = TemporalKV()
    kv.set("a", "v", 1)
    kv.delete("a", 5)
    assert kv.get("a", 5) is None
    assert kv.get("a", 10**9) is None


def test_same_timestamp_set_then_delete_get_is_none():
    kv = TemporalKV()
    kv.set("a", "v", 5)
    kv.delete("a", 5)
    assert kv.get("a", 5) is None
    assert kv.get("a", 6) is None


def test_same_timestamp_delete_then_set_get_is_value():
    kv = TemporalKV()
    kv.set("a", "old", 1)
    kv.delete("a", 5)
    kv.set("a", "new", 5)
    assert kv.get("a", 5) == "new"
    assert kv.get("a", 6) == "new"
    assert kv.get("a", 4) == "old"


def test_same_timestamp_set_then_delete_both_change_points():
    kv = TemporalKV()
    kv.set("a", "v", 5)
    kv.delete("a", 5)
    assert kv.get_range("a", 5, 5) == [(5, "v"), (5, None)]


def test_same_timestamp_delete_then_set_both_change_points():
    kv = TemporalKV()
    kv.delete("a", 5)
    kv.set("a", "v", 5)
    assert kv.get_range("a", 0, 10) == [(5, None), (5, "v")]


def test_delete_on_never_set_key_records_tombstone():
    kv = TemporalKV()
    kv.delete("fresh", 3)
    assert kv.get("fresh", 2) is None
    assert kv.get("fresh", 3) is None
    assert kv.get("fresh", 10) is None
    assert kv.get_range("fresh", 0, 10) == [(3, None)]


def test_get_range_single_point_window_on_a_delete():
    kv = _spec_kv()
    assert kv.get_range("a", 5, 5) == [(5, None)]


def test_get_range_window_with_no_changes_is_empty():
    kv = _spec_kv()
    assert kv.get_range("a", 6, 8) == []
    assert kv.get_range("a", 2, 4) == []


def test_get_range_full_window_lists_every_change_in_time_order():
    kv = _spec_kv()
    assert kv.get_range("a", 0, 100) == [(1, "v"), (5, None), (9, "w")]


def test_get_range_start_greater_than_end_is_empty():
    kv = _spec_kv()
    assert kv.get_range("a", 9, 1) == []
    assert kv.get_range("a", 100, 0) == []


def test_get_range_unknown_key_is_empty():
    kv = _spec_kv()
    assert kv.get_range("nope", 0, 100) == []


def test_get_range_on_unknown_key_does_not_create_an_entry():
    kv = TemporalKV()
    assert kv.get_range("ghost", 0, 100) == []
    assert kv.get("ghost", 50) is None
    assert kv.get_range("ghost", 0, 100) == []


def test_get_range_is_inclusive_at_both_ends():
    kv = _spec_kv()
    assert kv.get_range("a", 1, 9) == [(1, "v"), (5, None), (9, "w")]
    assert kv.get_range("a", 2, 9) == [(5, None), (9, "w")]
    assert kv.get_range("a", 1, 8) == [(1, "v"), (5, None)]
    assert kv.get_range("a", 2, 8) == [(5, None)]


def test_get_range_excludes_value_already_in_effect_before_start():
    kv = TemporalKV()
    kv.set("a", "v1", 1)
    kv.set("a", "v2", 5)
    assert kv.get("a", 3) == "v1"
    assert kv.get_range("a", 3, 10) == [(5, "v2")]


def test_get_range_only_includes_the_requested_key():
    kv = TemporalKV()
    kv.set("a", "va", 1)
    kv.set("b", "vb", 2)
    kv.delete("b", 3)
    kv.set("a", "va2", 4)
    assert kv.get_range("a", 0, 10) == [(1, "va"), (4, "va2")]
    assert kv.get_range("b", 0, 10) == [(2, "vb"), (3, None)]


def test_delete_does_not_affect_other_keys():
    kv = TemporalKV()
    kv.set("a", "va", 1)
    kv.set("b", "vb", 1)
    kv.delete("a", 2)
    assert kv.get("a", 2) is None
    assert kv.get("b", 2) == "vb"
