# Credit Tracker, Part 3: events arrive in any order; check_credit(t) replays
# every event with timestamp <= t and returns -1 if a subtraction was short.
# Run with: pytest credit_tracker -q

import random
import time

from credit_tracker import CreditTracker


def simulate(events: list[tuple], t: int) -> int:
    """Brute-force oracle. `events` in arrival order: ("add", start, end, amount)
    or ("sub", ts, amount). Replays events with ts <= t in (ts, arrival) order;
    returns the balance at t, or -1 if a subtraction was short."""
    timeline = sorted(((e[1], i, e) for i, e in enumerate(events)), key=lambda x: (x[0], x[1]))
    grants: list[list[int]] = []            # [start, end, remaining, arrival_idx]
    for ts, i, e in timeline:
        if ts > t:
            break
        if e[0] == "add":
            grants.append([e[1], e[2], e[3], i])
            continue
        need = e[2]
        for g in sorted((g for g in grants if g[0] <= ts <= g[1] and g[2] > 0), key=lambda g: (g[1], g[3])):
            take = min(g[2], need)
            g[2] -= take
            need -= take
            if need == 0:
                break
        if need > 0:
            return -1
    return sum(g[2] for g in grants if g[0] <= t <= g[1])


def feed(c: CreditTracker, events: list[tuple]) -> None:
    for e in events:
        if e[0] == "add":
            c.add_credit(e[1], e[2], e[3])
        else:
            c.subtract_credit(e[1], e[2])


def test_subtract_recorded_before_its_covering_add_is_short_until_the_add_arrives():
    c = CreditTracker()
    c.subtract_credit(6, 70)
    assert c.check_credit(6) == -1
    c.add_credit(1, 10, 100)
    assert c.check_credit(6) == 30


def test_check_before_a_recorded_subtraction_does_not_see_it():
    c = CreditTracker()
    c.subtract_credit(6, 70)
    c.add_credit(1, 10, 100)
    assert c.check_credit(5) == 100
    assert c.check_credit(6) == 30


def test_replay_draws_from_earliest_expiring_grant_first():
    # Same split as Part 2, but the sooner-expiring grant arrives last.
    c = CreditTracker()
    c.subtract_credit(6, 70)
    c.add_credit(1, 10, 100)
    c.add_credit(5, 7, 50)
    assert c.check_credit(6) == 80
    assert c.check_credit(8) == 80


def test_subtraction_after_a_grant_expired_is_short_only_for_checks_at_or_after_it():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.subtract_credit(11, 1)
    assert c.check_credit(10) == 100
    assert c.check_credit(11) == -1
    assert c.check_credit(100) == -1


def test_check_before_any_event_is_zero():
    c = CreditTracker()
    assert c.check_credit(0) == 0
    c.subtract_credit(5, 10)
    c.add_credit(3, 9, 10)
    assert c.check_credit(0) == 0
    assert c.check_credit(2) == 0


def test_same_timestamp_add_then_subtract_is_covered():
    c = CreditTracker()
    c.add_credit(2, 2, 5)
    c.subtract_credit(2, 5)
    assert c.check_credit(2) == 0
    assert c.check_credit(3) == 0


def test_same_timestamp_subtract_then_add_is_short():
    c = CreditTracker()
    c.subtract_credit(2, 5)
    c.add_credit(2, 2, 5)
    assert c.check_credit(2) == -1


def test_adds_arriving_in_reverse_time_order_sum_correctly():
    c = CreditTracker()
    c.add_credit(5, 7, 50)
    c.add_credit(1, 10, 100)
    assert [c.check_credit(t) for t in (0, 1, 5, 7, 8, 11)] == [0, 100, 150, 150, 100, 0]


def test_short_subtraction_stays_short_until_a_grant_that_covers_it_arrives():
    c = CreditTracker()
    c.subtract_credit(3, 10)
    assert c.check_credit(3) == -1
    assert c.check_credit(9) == -1
    c.add_credit(1, 2, 100)                 # expired before the subtraction: does not help
    assert c.check_credit(3) == -1
    c.add_credit(1, 5, 10)                  # covers it exactly
    assert c.check_credit(3) == 0
    assert c.check_credit(9) == 0


def test_grant_that_expired_before_t_is_still_replayed_for_earlier_subtractions():
    # If the replay dropped adds whose end < t, the subtraction at 2 would
    # look short when checking at 5.
    c = CreditTracker()
    c.add_credit(1, 2, 50)
    c.subtract_credit(2, 50)
    c.add_credit(4, 8, 7)
    assert c.check_credit(5) == 7
    assert c.check_credit(2) == 0


def test_check_is_repeatable_and_order_of_checks_does_not_matter():
    c = CreditTracker()
    c.add_credit(1, 10, 100)
    c.add_credit(5, 7, 50)
    c.subtract_credit(6, 70)
    assert c.check_credit(8) == 80
    assert c.check_credit(6) == 80
    assert c.check_credit(5) == 150
    assert c.check_credit(8) == 80
    assert c.check_credit(6) == 80


def test_check_result_does_not_depend_on_arrival_order():
    # Distinct timestamps, so insertion order never breaks a tie and the
    # replay must give the same answer however the events arrived.
    rng = random.Random(11)
    for trial in range(10):
        events: list[tuple] = []
        for ts in rng.sample(range(0, 120), 40):
            if rng.random() < 0.6:
                events.append(("add", ts, ts + rng.randint(0, 30), rng.randint(1, 30)))
            else:
                events.append(("sub", ts, rng.randint(1, 25)))
        in_order = sorted(events, key=lambda e: e[1])
        shuffled = events[:]
        rng.shuffle(shuffled)
        a, b = CreditTracker(), CreditTracker()
        feed(a, in_order)
        feed(b, shuffled)
        for t in range(0, 130, 3):
            expected = simulate(in_order, t)
            assert a.check_credit(t) == expected, (trial, t)
            assert b.check_credit(t) == expected, (trial, t, shuffled)


def test_random_out_of_order_events_match_brute_force():
    rng = random.Random(99)
    for trial in range(15):
        c = CreditTracker()
        events: list[tuple] = []
        for _ in range(50):
            if rng.random() < 0.6:
                s = rng.randint(0, 40)
                ev = ("add", s, s + rng.randint(0, 12), rng.randint(1, 40))
            else:
                ev = ("sub", rng.randint(0, 50), rng.randint(1, 30))
            events.append(ev)
            feed(c, [ev])
            t = rng.randint(0, 55)
            assert c.check_credit(t) == simulate(events, t), (trial, events, t)


def test_scale_20000_adds_5000_subtractions_random_order_then_200_checks_under_5_seconds():
    rng = random.Random(7)
    events: list[tuple] = []
    for _ in range(20_000):
        s = rng.randint(0, 1_000_000)
        events.append(("add", s, s + rng.randint(0, 5_000), rng.randint(1, 100)))
    for _ in range(5_000):
        events.append(("sub", rng.randint(0, 1_000_000), rng.randint(1, 100)))
    rng.shuffle(events)
    c = CreditTracker()
    started = time.perf_counter()
    feed(c, events)
    results = [c.check_credit(rng.randint(0, 1_000_000)) for _ in range(200)]
    elapsed = time.perf_counter() - started
    assert elapsed < 5.0, f"25,000 events plus 200 checks took {elapsed:.2f}s"
    assert all(isinstance(r, int) and r >= -1 for r in results)
    assert c.check_credit(-1) == 0
