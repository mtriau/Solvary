# Provided tests for Part 1: tiers and a default policy.

import rate_limiter as rl

TIERS = {"free": (3, 1.0), "pro": (10, 5.0), "fast": (2, 2.0)}


def drain(limiter, client, now, n):
    return [limiter.allow(client, now) for _ in range(n)]


def test_spec_example():
    limiter = rl.RateLimiter(TIERS)
    limiter.set_client_tier("alice", "free")
    assert [limiter.allow("alice", 0.0) for _ in range(4)] == [True, True, True, False]
    assert limiter.allow("alice", 1.0) is True
    assert limiter.allow("alice", 1.0) is False


def test_buckets_start_full_and_burst_is_exactly_capacity():
    limiter = rl.RateLimiter(TIERS)
    limiter.set_client_tier("bob", "pro")
    results = drain(limiter, "bob", 100.0, 12)
    assert results == [True] * 10 + [False] * 2


def test_clients_have_independent_buckets():
    limiter = rl.RateLimiter(TIERS)
    limiter.set_client_tier("a", "free")
    limiter.set_client_tier("b", "free")
    assert drain(limiter, "a", 0.0, 3) == [True] * 3
    assert limiter.allow("a", 0.0) is False
    assert limiter.allow("b", 0.0) is True


def test_fractional_refill_one_token_after_half_second_at_rate_two():
    limiter = rl.RateLimiter(TIERS)
    limiter.set_client_tier("c", "fast")
    assert drain(limiter, "c", 0.0, 2) == [True, True]
    assert limiter.allow("c", 0.4) is False  # 0.8 of a token
    assert limiter.allow("c", 0.5) is True  # 1.0 token
    assert limiter.allow("c", 0.5) is False


def test_never_more_than_capacity_after_a_long_idle():
    limiter = rl.RateLimiter(TIERS)
    limiter.set_client_tier("d", "free")
    assert drain(limiter, "d", 0.0, 3) == [True] * 3
    assert drain(limiter, "d", 10_000.0, 5) == [True] * 3 + [False] * 2


def test_unknown_client_without_default_is_denied():
    limiter = rl.RateLimiter(TIERS)
    assert drain(limiter, "ghost", 0.0, 3) == [False] * 3
    assert limiter.allow("ghost", 1_000_000.0) is False


def test_unknown_client_uses_the_default_tier():
    limiter = rl.RateLimiter(TIERS, default="free")
    assert drain(limiter, "ghost", 0.0, 4) == [True, True, True, False]
    assert limiter.allow("ghost2", 0.0) is True  # its own bucket


def test_unknown_tier_name_falls_back_to_default_or_denies():
    with_default = rl.RateLimiter(TIERS, default="fast")
    with_default.set_client_tier("x", "platinum")
    assert drain(with_default, "x", 0.0, 3) == [True, True, False]
    without = rl.RateLimiter(TIERS)
    without.set_client_tier("x", "platinum")
    assert without.allow("x", 0.0) is False


def test_default_that_is_not_a_known_tier_fails_closed():
    limiter = rl.RateLimiter(TIERS, default="nope")
    assert limiter.allow("anyone", 0.0) is False


def test_clock_going_backwards_for_a_client_neither_refills_nor_errors():
    limiter = rl.RateLimiter({"t": (1, 1.0)})
    limiter.set_client_tier("c", "t")
    assert limiter.allow("c", 10.0) is True
    assert limiter.allow("c", 5.0) is False  # earlier time: no refill, no crash
    assert limiter.allow("c", 10.5) is False  # still measured from t=10
    assert limiter.allow("c", 11.0) is True
