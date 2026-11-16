# Provided tests for Part 2: update within the window.

import csat_tracker
import pytest


def make(window=5):
    return csat_tracker.CSATTracker(window)


def test_update_active_conversation_returns_true():
    t = make()
    t.record("a", 2, 10)
    assert t.update("a", 5, 12) is True


def test_update_changes_the_average():
    t = make(100)
    t.record("a", 2, 1)
    t.record("b", 4, 2)
    assert t.get_average(2) == 3.0
    assert t.update("a", 5, 3) is True
    assert t.get_average(3) == 4.5


def test_update_to_same_score_is_still_true():
    t = make(100)
    t.record("a", 3, 1)
    assert t.update("a", 3, 2) is True
    assert t.get_average(2) == 3.0


def test_update_expired_conversation_is_a_noop():
    t = make(5)
    t.record("a", 1, 10)
    t.record("b", 5, 14)
    assert t.update("a", 5, 16) is False  # 16 - 10 = 6 > 5
    assert t.get_average(16) == 5.0


def test_update_boundary_is_inclusive():
    t = make(5)
    t.record("a", 1, 10)
    assert t.update("a", 4, 15) is True
    assert t.get_average(15) == 4.0
    assert t.update("a", 2, 16) is False
    assert t.get_average(16) == 0.0


def test_update_unknown_conversation_returns_false():
    t = make()
    t.record("a", 3, 1)
    assert t.update("zzz", 4, 2) is False
    assert t.get_average(2) == 3.0


def test_update_on_empty_tracker_returns_false():
    assert make().update("a", 3, 1) is False


def test_updated_conversation_keeps_its_original_expiry():
    t = make(5)
    t.record("a", 1, 10)
    t.record("b", 3, 14)
    assert t.update("a", 5, 15) is True  # updating at 15 does not renew it
    assert t.get_average(15) == 4.0
    assert t.get_average(16) == 3.0  # "a" still leaves at 16


def test_update_can_be_repeated():
    t = make(100)
    t.record("a", 1, 1)
    t.update("a", 2, 2)
    t.update("a", 5, 3)
    t.update("a", 4, 4)
    assert t.get_average(4) == 4.0


def test_update_invalid_score_raises_and_changes_nothing():
    t = make(100)
    t.record("a", 3, 1)
    for bad in (0, 6, 2.5, "3"):
        with pytest.raises(ValueError):
            t.update("a", bad, 2)
    assert t.get_average(2) == 3.0


def test_update_after_expiry_does_not_resurrect():
    t = make(3)
    t.record("a", 5, 1)
    assert t.get_average(10) == 0.0
    assert t.update("a", 1, 10) is False
    assert t.get_average(10) == 0.0


def test_update_then_record_later_mixes_correctly():
    t = make(10)
    t.record("a", 2, 1)
    t.record("b", 2, 2)
    t.update("b", 5, 3)
    t.record("c", 3, 4)
    assert t.get_average(4) == 3.33
    assert t.get_average(12) == 4.0  # "a" gone: (5 + 3) / 2
