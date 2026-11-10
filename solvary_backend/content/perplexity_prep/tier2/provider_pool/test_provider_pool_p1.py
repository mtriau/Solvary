# Tier 2 #1: ProviderPool. Run with: pytest tier2/test_provider_pool.py -q

import pytest

from provider_pool import ProviderPool


def make_pool() -> ProviderPool:
    pool = ProviderPool()
    pool.add_provider("openai", priority=1, capabilities={"chat", "embed"})
    pool.add_provider("anthropic", priority=2, capabilities={"chat"})
    pool.add_provider("local", priority=3, capabilities={"chat", "embed"})
    return pool


def test_spec_example():
    pool = make_pool()
    assert pool.route("chat") == "openai"
    pool.report_failure("openai")
    pool.report_failure("openai")
    pool.report_failure("openai")
    assert pool.route("chat") == "anthropic"
    assert pool.route("embed") == "local"
    pool.report_success("openai")
    assert pool.route("chat") == "openai"
    assert pool.route("video") is None


def test_route_picks_lowest_priority_number_regardless_of_add_order():
    pool = ProviderPool()
    pool.add_provider("slow", priority=5, capabilities={"chat"})
    pool.add_provider("fast", priority=1, capabilities={"chat"})
    pool.add_provider("medium", priority=3, capabilities={"chat"})
    assert pool.route("chat") == "fast"


def test_route_skips_providers_without_the_capability():
    pool = make_pool()
    assert pool.route("embed") == "openai"
    pool.report_failure("openai")
    pool.report_failure("openai")
    pool.report_failure("openai")
    # anthropic is healthier and higher priority but cannot embed
    assert pool.route("embed") == "local"


def test_route_returns_none_when_no_provider_has_the_capability():
    pool = make_pool()
    assert pool.route("video") is None
    assert ProviderPool().route("chat") is None


def test_route_returns_none_when_all_capable_providers_are_unhealthy():
    pool = ProviderPool()
    pool.add_provider("a", priority=1, capabilities={"embed"}, failure_threshold=1)
    pool.add_provider("b", priority=2, capabilities={"embed"}, failure_threshold=1)
    pool.add_provider("c", priority=3, capabilities={"chat"})
    pool.report_failure("a")
    pool.report_failure("b")
    assert pool.route("embed") is None
    assert pool.route("chat") == "c"


def test_provider_becomes_unhealthy_at_exactly_threshold_failures():
    pool = make_pool()
    pool.report_failure("openai")
    pool.report_failure("openai")
    assert pool.route("chat") == "openai"        # 2 of 3: still healthy
    pool.report_failure("openai")
    assert pool.route("chat") == "anthropic"     # exactly 3: unhealthy


def test_custom_failure_threshold_is_respected():
    pool = ProviderPool()
    pool.add_provider("fragile", priority=1, capabilities={"chat"}, failure_threshold=1)
    pool.add_provider("sturdy", priority=2, capabilities={"chat"}, failure_threshold=5)
    pool.report_failure("fragile")
    assert pool.route("chat") == "sturdy"
    for _ in range(4):
        pool.report_failure("sturdy")
    assert pool.route("chat") == "sturdy"        # 4 of 5: still healthy
    pool.report_failure("sturdy")
    assert pool.route("chat") is None


def test_success_resets_failure_count_to_zero_not_by_one():
    pool = make_pool()
    pool.report_failure("openai")
    pool.report_failure("openai")
    pool.report_success("openai")
    pool.report_failure("openai")
    pool.report_failure("openai")
    assert pool.route("chat") == "openai"        # 2 fresh failures after the reset
    pool.report_failure("openai")
    assert pool.route("chat") == "anthropic"


def test_success_restores_an_unhealthy_provider_even_after_many_failures():
    pool = make_pool()
    for _ in range(10):
        pool.report_failure("openai")
    assert pool.route("chat") == "anthropic"
    pool.report_success("openai")
    assert pool.route("chat") == "openai"


def test_failures_are_counted_per_provider():
    pool = make_pool()
    for _ in range(3):
        pool.report_failure("anthropic")
    assert pool.route("chat") == "openai"
    for _ in range(3):
        pool.report_failure("openai")
    assert pool.route("chat") == "local"


def test_equal_priority_ties_break_by_insertion_order():
    pool = ProviderPool()
    pool.add_provider("second", priority=1, capabilities={"chat"})
    pool.add_provider("first", priority=1, capabilities={"chat"})
    assert pool.route("chat") == "second"
    for _ in range(3):
        pool.report_failure("second")
    assert pool.route("chat") == "first"


def test_readding_a_name_replaces_priority_and_capabilities():
    pool = make_pool()
    pool.add_provider("local", priority=0, capabilities={"video"})
    assert pool.route("video") == "local"
    assert pool.route("embed") == "openai"
    for _ in range(3):
        pool.report_failure("openai")
    assert pool.route("embed") is None           # local no longer embeds
    assert pool.route("chat") == "anthropic"     # and no longer chats


def test_readding_a_name_resets_its_health():
    pool = make_pool()
    for _ in range(3):
        pool.report_failure("openai")
    assert pool.route("chat") == "anthropic"
    pool.add_provider("openai", priority=1, capabilities={"chat", "embed"})
    assert pool.route("chat") == "openai"
    pool.report_failure("openai")
    pool.report_failure("openai")
    assert pool.route("chat") == "openai"        # the old failures did not carry over


def test_report_on_unknown_name_raises_value_error():
    pool = make_pool()
    with pytest.raises(ValueError):
        pool.report_failure("nope")
    with pytest.raises(ValueError):
        pool.report_success("nope")


def test_separate_pools_do_not_share_providers():
    a = make_pool()
    b = ProviderPool()
    assert b.route("chat") is None
    for _ in range(3):
        a.report_failure("openai")
    b.add_provider("openai", priority=1, capabilities={"chat"})
    assert b.route("chat") == "openai"
    assert a.route("chat") == "anthropic"
