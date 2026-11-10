# Provided tests for Part 2: compact a history to a token budget.

from conversation_history import Message, compact

_n = 0


def m(role: str, tokens: int) -> Message:
    global _n
    _n += 1
    return Message(id=f"m{_n}", role=role, text=role, tokens=tokens)


def spec_history():
    return [m("system", 5), m("user", 10), m("assistant", 10), m("user", 10)]


def test_under_budget_is_unchanged():
    msgs = spec_history()
    assert compact(msgs, 100) == msgs


def test_exactly_at_budget_is_unchanged():
    msgs = spec_history()
    assert compact(msgs, 35) == msgs


def test_drops_oldest_non_system_first():
    msgs = spec_history()
    assert compact(msgs, 34) == [msgs[0], msgs[2], msgs[3]]


def test_keeps_dropping_until_it_fits():
    msgs = spec_history()
    assert compact(msgs, 20) == [msgs[0], msgs[3]]


def test_system_message_is_never_dropped():
    msgs = spec_history()
    out = compact(msgs, 3)
    assert msgs[0] in out
    assert out == [msgs[0], msgs[3]]


def test_most_recent_message_is_never_dropped_even_if_oversized():
    msgs = [m("user", 1), m("user", 1), m("user", 500)]
    assert compact(msgs, 10) == [msgs[2]]


def test_system_messages_anywhere_are_pinned():
    msgs = [m("user", 10), m("system", 10), m("user", 10), m("system", 10), m("user", 10)]
    assert compact(msgs, 30) == [msgs[1], msgs[3], msgs[4]]


def test_no_system_message():
    msgs = [m("user", 4), m("assistant", 4), m("user", 4)]
    assert compact(msgs, 8) == msgs[1:]


def test_empty_history():
    assert compact([], 10) == []


def test_single_message_over_budget_is_kept():
    only = m("user", 99)
    assert compact([only], 1) == [only]


def test_does_not_mutate_input():
    msgs = spec_history()
    snapshot = list(msgs)
    compact(msgs, 10)
    assert msgs == snapshot


def test_returns_a_fresh_list_when_unchanged():
    msgs = spec_history()
    out = compact(msgs, 1000)
    out.append(m("user", 1))
    assert len(msgs) == 4


def test_zero_token_messages_are_still_messages():
    msgs = [m("user", 0), m("user", 0), m("user", 5), m("user", 5)]
    assert compact(msgs, 5) == [msgs[3]]
    assert compact(msgs, 10) == msgs
