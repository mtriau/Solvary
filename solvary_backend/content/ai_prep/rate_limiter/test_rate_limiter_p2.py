# Provided tests for Part 2: runtime updates.

import rate_limiter as rl


def make(**kw):
    return rl.RateLimiter({"free": (3, 1.0), "pro": (10, 5.0)}, **kw)


def count(limiter, client, now, n=50):
    return sum(limiter.allow(client, now) for _ in range(n))


def test_raising_capacity_does_not_grant_tokens():
    limiter = make()
    limiter.set_client_tier("a", "free")
    assert limiter.allow("a", 0.0) is True  # 2 left
    limiter.update_tier("free", 100, 1.0)
    assert count(limiter, "a", 0.0) == 2


def test_raised_capacity_is_reachable_by_refilling():
    limiter = make()
    limiter.set_client_tier("a", "free")
    assert count(limiter, "a", 0.0) == 3
    limiter.update_tier("free", 100, 1.0)
    assert count(limiter, "a", 0.0) == 0
    assert count(limiter, "a", 20.0) == 20


def test_cutting_capacity_truncates_existing_tokens():
    limiter = make()
    limiter.set_client_tier("a", "pro")
    assert limiter.allow("a", 0.0) is True  # 9 left
    limiter.update_tier("pro", 2, 5.0)
    assert count(limiter, "a", 0.0) == 2
    assert count(limiter, "a", 1000.0) == 2  # and the cap holds from now on


def test_new_rate_applies_from_now_on():
    limiter = make()
    limiter.set_client_tier("a", "free")
    assert count(limiter, "a", 0.0) == 3
    limiter.update_tier("free", 3, 10.0)
    assert limiter.allow("a", 0.1) is True  # 10/s * 0.1s = one token
    assert limiter.allow("a", 0.1) is False


def test_update_affects_every_client_in_the_tier_and_only_that_tier():
    limiter = make()
    for c in ("a", "b"):
        limiter.set_client_tier(c, "free")
        assert limiter.allow(c, 0.0) is True
    limiter.set_client_tier("p", "pro")
    assert limiter.allow("p", 0.0) is True
    limiter.update_tier("free", 1, 1.0)
    assert count(limiter, "a", 0.0) == 1
    assert count(limiter, "b", 0.0) == 1
    assert count(limiter, "p", 0.0) == 9


def test_update_reaches_clients_that_use_the_default_tier():
    limiter = make(default="free")
    assert count(limiter, "ghost", 0.0) == 3
    limiter.update_tier("free", 3, 4.0)
    assert limiter.allow("ghost", 0.5) is True
    assert limiter.allow("ghost", 0.5) is True
    assert limiter.allow("ghost", 0.5) is False


def test_update_tier_can_create_a_tier_a_client_was_already_assigned_to():
    limiter = make()
    limiter.set_client_tier("a", "gold")
    assert limiter.allow("a", 0.0) is False  # unknown tier, no default
    limiter.update_tier("gold", 2, 1.0)
    assert count(limiter, "a", 0.0) == 2


def test_moving_a_client_to_a_bigger_tier_keeps_its_tokens():
    limiter = make()
    limiter.set_client_tier("a", "free")
    assert limiter.allow("a", 0.0) and limiter.allow("a", 0.0)  # 1 token left
    limiter.set_client_tier("a", "pro")
    assert count(limiter, "a", 0.0) == 1  # not 10


def test_moving_a_client_to_a_smaller_tier_clamps_its_tokens():
    limiter = make()
    limiter.set_client_tier("a", "pro")
    assert limiter.allow("a", 0.0) is True  # 9 left
    limiter.set_client_tier("a", "free")
    assert count(limiter, "a", 0.0) == 3


def test_remove_client_forgets_tier_and_bucket():
    limiter = make()
    limiter.set_client_tier("a", "free")
    assert count(limiter, "a", 0.0) == 3
    limiter.remove_client("a")
    assert limiter.allow("a", 0.0) is False  # no tier, no default
    limiter.set_client_tier("a", "free")
    assert count(limiter, "a", 0.0) == 3  # fresh, full bucket


