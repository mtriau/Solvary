# Credit Tracker, Part 2: subtract_credit(t, amount) -> int, earliest-expiry
# first; calls arrive in non-decreasing time order.
# Run with: pytest credit_tracker -q

import random

from credit_tracker import CreditTracker


def simulate(events: list[tuple], t: int) -> tuple[int, dict[int, int]]:
    """Brute-force oracle. `events` in arrival order: ("add", start, end, amount)
    or ("sub", ts, amount). Replays events with ts <= t in (ts, arrival) order.
    Returns (balance at t, or -1 if a subtraction was short; {event_index: spent})."""
    timeline = sorted(((e[1], i, e) for i, e in enumerate(events)), key=lambda x: (x[0], x[1]))
    grants: list[list[int]] = []            # [start, end, remaining, arrival_idx]
    spent_by: dict[int, int] = {}
    short = False
    for ts, i, e in timeline:
        if ts > t:
            break
        if e[0] == "add":
            grants.append([e[1], e[2], e[3], i])
            continue
        need = e[2]
        spent = 0
        for g in sorted((g for g in grants if g[0] <= ts <= g[1] and g[2] > 0), key=lambda g: (g[1], g[3])):
            take = min(g[2], need)
            g[2] -= take
            need -= take
            spent += take
            if need == 0:
                break
        spent_by[i] = spent
        if need > 0:
            short = True
    if short:
        return -1, spent_by
    return sum(g[2] for g in grants if g[0] <= t <= g[1]), spent_by


def test_subtract_returns_the_amount_spent_when_fully_covered():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    assert c.subtract_credit(2, 30) == 30
    assert c.check_credit(2) == 70


def test_subtract_draws_from_earliest_expiring_grant_first():
    # (5..7) expires before (1..10), so the 70 is 50 from (5..7) + 20 from (1..10).
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.add_credit(5, 7, 50)
    assert c.subtract_credit(6, 70) == 70
    assert c.check_credit(6) == 80
    # After (5..7) expires, only (1..10) is left: it must still hold 80, not 30.
    assert c.check_credit(8) == 80


def test_subtract_draws_from_earliest_expiring_grant_even_if_added_later():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.add_credit(2, 3, 10)
    assert c.subtract_credit(3, 10) == 10
    assert c.check_credit(4) == 100


def test_partial_spend_returns_only_what_was_available():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.add_credit(5, 7, 50)
    assert c.subtract_credit(6, 70) == 70
    assert c.subtract_credit(8, 500) == 80
    assert c.subtract_credit(9, 1) == 0


def test_subtract_with_nothing_active_returns_zero():
    c = CreditTracker()
    assert c.subtract_credit(1, 5) == 0


def test_subtract_after_every_grant_expired_returns_zero():
    c = CreditTracker()
    c.add_credit(3, 4, 10)
    assert c.check_credit(5) == 0
    assert c.subtract_credit(5, 5) == 0
    assert c.subtract_credit(6, 5) == 0


def test_subtract_exactly_at_end_draws_from_the_grant():
    c = CreditTracker()
    c.add_credit(1, 3, 10)
    assert c.subtract_credit(3, 4) == 4
    assert c.check_credit(3) == 6
    assert c.check_credit(4) == 0


def test_subtract_at_the_same_time_as_the_grant_start_can_use_it():
    c = CreditTracker()
    c.add_credit(5, 9, 10)
    assert c.subtract_credit(5, 10) == 10
    assert c.check_credit(5) == 0


def test_partial_spend_leaves_the_grant_with_the_remainder():
    c = CreditTracker()
    c.add_credit(1, 5, 10)
    assert c.subtract_credit(2, 4) == 4
    assert c.check_credit(2) == 6
    assert c.check_credit(5) == 6
    assert c.check_credit(6) == 0


def test_spent_credit_stays_gone_for_all_later_times():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.subtract_credit(2, 40)
    assert c.check_credit(3) == 60
    assert c.check_credit(10) == 60
    assert c.check_credit(11) == 0


def test_subtract_does_not_charge_grants_that_have_already_expired():
    # (1..2) would be first by end time, but it is gone at t=3: the 5 must
    # come out of (1..10), leaving 5 there.
    c = CreditTracker()
    c.add_credit(1, 2, 50)
    c.add_credit(1, 10, 10)
    assert c.subtract_credit(3, 5) == 5
    assert c.check_credit(3) == 5


def test_repeated_subtractions_drain_grants_in_expiry_order():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.add_credit(2, 4, 30)
    c.add_credit(3, 6, 20)
    assert c.subtract_credit(3, 40) == 40      # 30 from (2..4), 10 from (3..6)
    assert c.check_credit(3) == 110
    assert c.check_credit(5) == 110            # (2..4) expired with nothing left anyway
    assert c.subtract_credit(5, 15) == 15      # 10 from (3..6), 5 from (1..10)
    assert c.check_credit(7) == 95             # only (1..10) is left
    assert c.subtract_credit(7, 95) == 95
    assert c.check_credit(7) == 0
    assert c.subtract_credit(8, 1) == 0


def test_tie_on_end_time_spends_across_both_grants_without_double_counting():
    c = CreditTracker()
    c.add_credit(1, 5, 10)
    c.add_credit(2, 5, 10)
    assert c.subtract_credit(3, 15) == 15
    assert c.check_credit(3) == 5
    assert c.check_credit(5) == 5
    assert c.check_credit(6) == 0


def test_check_does_not_spend_anything():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    for _ in range(5):
        assert c.check_credit(5) == 100
    assert c.subtract_credit(5, 100) == 100


def test_random_time_ordered_sequence_matches_brute_force():
    rng = random.Random(2024)
    for trial in range(20):
        c = CreditTracker()
        events: list[tuple] = []
        now = 0
        for _ in range(60):
            now += rng.randint(0, 3)
            if rng.random() < 0.5:
                ev = ("add", now, now + rng.randint(0, 8), rng.randint(1, 50))
                c.add_credit(ev[1], ev[2], ev[3])
                events.append(ev)
            else:
                ev = ("sub", now, rng.randint(1, 40))
                events.append(ev)
                spent = c.subtract_credit(now, ev[2])
                balance, spent_by = simulate(events, now)
                assert spent == spent_by[len(events) - 1], (trial, events)
                if balance == -1:
                    break                      # a short subtraction happened: stop this trial
                assert c.check_credit(now) == balance, (trial, events)
