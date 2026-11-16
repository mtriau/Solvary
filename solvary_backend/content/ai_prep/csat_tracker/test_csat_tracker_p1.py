# Provided tests for Part 1: record and get_average.

import csat_tracker
import pytest


def make(window=5):
    return csat_tracker.CSATTracker(window)


def test_empty_tracker_average_is_zero():
    assert make().get_average(100) == 0.0


def test_single_score_average():
    t = make()
    t.record("a", 4, 10)
    assert t.get_average(10) == 4.0


def test_average_of_several_scores():
    t = make(100)
    t.record("a", 5, 1)
    t.record("b", 3, 2)
    assert t.get_average(2) == 4.0


def test_average_rounds_to_two_places():
    t = make(100)
    t.record("a", 4, 1)
    t.record("b", 4, 2)
    t.record("c", 5, 3)
    assert t.get_average(3) == 4.33


def test_boundary_is_inclusive():
    t = make(5)
    t.record("a", 5, 10)
    assert t.get_average(15) == 5.0  # 15 - 10 == 5, still active


def test_expires_one_tick_after_boundary():
    t = make(5)
    t.record("a", 5, 10)
    assert t.get_average(16) == 0.0  # 16 - 10 == 6 > 5


def test_old_scores_leave_the_average():
    t = make(5)
    t.record("a", 1, 10)
    t.record("b", 5, 14)
    assert t.get_average(14) == 3.0
    assert t.get_average(16) == 5.0  # "a" expired, "b" active
    assert t.get_average(19) == 5.0  # 19 - 14 == 5
    assert t.get_average(20) == 0.0


def test_window_zero_keeps_only_the_current_instant():
    t = make(0)
    t.record("a", 3, 7)
    assert t.get_average(7) == 3.0
    assert t.get_average(8) == 0.0


def test_invalid_score_raises():
    for bad in [0, 6, -1, 3.5, "4", None]:
        t = make()
        with pytest.raises(ValueError):
            t.record("a", bad, 1)


def test_invalid_record_leaves_state_untouched():
    t = make(100)
    t.record("a", 4, 5)
    with pytest.raises(ValueError):
        t.record("b", 9, 6)
    with pytest.raises(ValueError):
        t.record("c", 1, 5)
    assert t.get_average(6) == 4.0
    t.record("b", 2, 6)  # ids and timestamps from failed calls are still free
    t.record("c", 2, 7)
    assert t.get_average(7) == 2.67


def test_non_increasing_timestamp_raises():
    t = make()
    t.record("a", 3, 10)
    with pytest.raises(ValueError):
        t.record("b", 3, 10)
    with pytest.raises(ValueError):
        t.record("c", 3, 9)


def test_duplicate_conversation_id_raises():
    t = make()
    t.record("a", 3, 10)
    with pytest.raises(ValueError):
        t.record("a", 4, 11)


def test_duplicate_id_still_raises_after_expiry():
    t = make(2)
    t.record("a", 3, 1)
    assert t.get_average(50) == 0.0
    with pytest.raises(ValueError):
        t.record("a", 3, 51)
