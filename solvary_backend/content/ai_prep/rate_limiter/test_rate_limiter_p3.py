# Provided tests for Part 3: injectable clock and observability.

import math

import pytest

import rate_limiter as rl


class FakeClock:
    def __init__(self, start=0.0):
        self.now = start
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.now

    def advance(self, dt):
        self.now += dt


def make(tiers=None, clock=None, **kw):
    tiers = tiers or {"t": (4, 2.0)}
    limiter = rl.RateLimiter(tiers, clock=clock, **kw)
    limiter.set_client_tier("c", next(iter(tiers)))
    return limiter


def test_allow_without_now_reads_the_clock():
    clock = FakeClock()
    limiter = make({"t": (2, 1.0)}, clock)
    assert [limiter.allow("c") for _ in range(3)] == [True, True, False]
    clock.advance(1.0)
    assert limiter.allow("c") is True
    assert limiter.allow("c") is False


def test_explicit_now_wins_and_the_clock_is_not_consulted():
    clock = FakeClock()
    limiter = make({"t": (1, 1.0)}, clock)
    assert limiter.allow("c", 0.0) is True
    assert limiter.allow("c", 5.0) is True  # refilled by the explicit time
    assert clock.calls == 0


def test_no_now_and_no_clock_is_an_error():
    limiter = make({"t": (1, 1.0)})
    with pytest.raises(ValueError):
        limiter.allow("c")


def test_mixing_explicit_now_and_clock_follows_the_backwards_rule():
    clock = FakeClock(0.0)
    limiter = make({"t": (1, 1.0)}, clock)
    assert limiter.allow("c", 10.0) is True
    assert limiter.allow("c") is False  # clock says 0.0, which is in the past
    clock.now = 10.5
    assert limiter.allow("c") is False
    clock.now = 11.0
    assert limiter.allow("c") is True


def test_tokens_reports_fractions_after_refill_without_consuming():
    clock = FakeClock()
    limiter = make(clock=clock)  # capacity 4, rate 2
    assert limiter.tokens("c") == pytest.approx(4.0)
    for _ in range(4):
        assert limiter.allow("c") is True
    assert limiter.tokens("c") == pytest.approx(0.0)
    clock.advance(0.25)
    assert limiter.tokens("c") == pytest.approx(0.5)
    assert limiter.tokens("c") == pytest.approx(0.5)  # reading twice changes nothing
    clock.advance(0.25)
    assert limiter.allow("c") is True
    assert limiter.tokens("c") == pytest.approx(0.0)


def test_tokens_never_exceeds_capacity():
    clock = FakeClock()
    limiter = make(clock=clock)
    limiter.allow("c")
    clock.advance(10_000)
    assert limiter.tokens("c") == pytest.approx(4.0)


def test_tokens_for_a_denied_client_is_zero():
    limiter = rl.RateLimiter({"t": (4, 2.0)}, clock=FakeClock())
    assert limiter.tokens("ghost") == 0.0
    limiter.set_client_tier("ghost", "nope")
    assert limiter.tokens("ghost") == 0.0


def test_retry_after_exact_values():
    clock = FakeClock()
    limiter = make({"t": (2, 0.5)}, clock)
    assert limiter.retry_after("c") == 0.0
    assert limiter.allow("c") and limiter.allow("c")
    assert limiter.retry_after("c") == pytest.approx(2.0)
    clock.advance(0.5)
    assert limiter.retry_after("c") == pytest.approx(1.5)
    clock.advance(1.5)
    assert limiter.retry_after("c") == 0.0


def test_waiting_exactly_retry_after_makes_the_next_request_pass():
    clock = FakeClock()
    limiter = make({"t": (3, 0.7)}, clock)
    while limiter.allow("c"):
        pass
    wait = limiter.retry_after("c")
    assert wait > 0
    clock.advance(wait * 0.9)
    assert limiter.allow("c") is False
    clock.advance(wait * 0.1)
    assert limiter.allow("c") is True


def test_retry_after_does_not_consume_and_is_infinite_when_it_can_never_pass():
    clock = FakeClock()
    limiter = make({"t": (1, 1.0)}, clock)
    for _ in range(3):
        assert limiter.retry_after("c") == 0.0
    assert limiter.allow("c") is True
    assert math.isinf(limiter.retry_after("ghost"))  # fail closed: never
    frozen = rl.RateLimiter({"z": (1, 0.0)}, clock=clock)
    frozen.set_client_tier("c", "z")
    assert frozen.allow("c") is True
    assert math.isinf(frozen.retry_after("c"))


def test_a_virtual_hundred_seconds_runs_instantly():
    clock = FakeClock()
    limiter = make({"t": (20, 10.0)}, clock)
    allowed = 0
    for _ in range(10_000):  # one request every 10 ms
        allowed += limiter.allow("c")
        clock.advance(0.01)
    assert 1018 <= allowed <= 1021  # 20 burst + 10/s * ~100 s
