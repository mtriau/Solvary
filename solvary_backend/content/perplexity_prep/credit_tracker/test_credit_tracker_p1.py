# Credit Tracker, Part 1: add_credit(start, end, amount) / check_credit(t).
# Run with: pytest credit_tracker -q

from credit_tracker import CreditTracker


def test_spec_example():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.add_credit(5, 7, 50)
    assert c.check_credit(0) == 0
    assert c.check_credit(1) == 100
    assert c.check_credit(5) == 150
    assert c.check_credit(7) == 150
    assert c.check_credit(8) == 100
    assert c.check_credit(11) == 0


def test_check_on_a_fresh_tracker_is_zero():
    c = CreditTracker()
    assert c.check_credit(0) == 0
    assert c.check_credit(123) == 0


def test_grant_is_active_at_exactly_start():
    c = CreditTracker()
    c.add_credit(10, 20, 5)
    assert c.check_credit(9) == 0
    assert c.check_credit(10) == 5


def test_grant_is_active_at_exactly_end():
    c = CreditTracker()
    c.add_credit(10, 20, 5)
    assert c.check_credit(20) == 5
    assert c.check_credit(21) == 0


def test_grant_with_start_equal_to_end_is_active_for_that_single_instant():
    c = CreditTracker()
    c.add_credit(3, 3, 7)
    assert c.check_credit(2) == 0
    assert c.check_credit(3) == 7
    assert c.check_credit(4) == 0


def test_two_grants_with_identical_windows_sum():
    c = CreditTracker()
    c.add_credit(1, 5, 10)
    c.add_credit(1, 5, 10)
    assert c.check_credit(1) == 20
    assert c.check_credit(5) == 20
    assert c.check_credit(6) == 0


def test_overlapping_grants_sum_only_where_both_are_active():
    c = CreditTracker()
    c.add_credit(1, 4, 10)
    c.add_credit(3, 6, 20)
    assert [c.check_credit(t) for t in range(0, 8)] == [0, 10, 10, 30, 30, 20, 20, 0]


def test_check_before_everything_and_after_everything_is_zero():
    c = CreditTracker()
    c.add_credit(5, 7, 50)
    c.add_credit(6, 9, 30)
    assert c.check_credit(4) == 0
    assert c.check_credit(10) == 0


def test_grants_that_do_not_overlap_never_add_up():
    c = CreditTracker()
    c.add_credit(1, 2, 10)
    c.add_credit(3, 4, 20)
    assert c.check_credit(2) == 10
    assert c.check_credit(3) == 20


def test_many_small_grants_add_up():
    c = CreditTracker()
    for i in range(100):
        c.add_credit(i, 200, 1)
    assert c.check_credit(50) == 51
    assert c.check_credit(200) == 100
    assert c.check_credit(201) == 0


def test_separate_trackers_do_not_share_grants():
    a = CreditTracker()
    b = CreditTracker()
    a.add_credit(1, 10, 100)
    assert a.check_credit(5) == 100
    assert b.check_credit(5) == 0
