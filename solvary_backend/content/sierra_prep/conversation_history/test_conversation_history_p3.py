# Provided tests for Part 3: incremental History with tool-call units.

from conversation_history import History, Message

_n = 0


def m(role: str, tokens: int, call_id: str | None = None) -> Message:
    global _n
    _n += 1
    return Message(id=f"m{_n}", role=role, text=role, tokens=tokens, call_id=call_id)


def fill(h: History, msgs):
    for x in msgs:
        h.append(x)
    return msgs


def test_under_budget_keeps_everything_in_order():
    h = History(limit=100)
    msgs = fill(h, [m("system", 5), m("user", 10), m("assistant", 10)])
    assert h.messages() == msgs
    assert h.total_tokens() == 25


def test_drops_oldest_when_over_budget():
    h = History(limit=20)
    msgs = fill(h, [m("user", 10), m("assistant", 10), m("user", 10)])
    assert h.messages() == msgs[1:]
    assert h.total_tokens() == 20


def test_system_message_is_pinned_and_order_is_append_order():
    h = History(limit=25)
    msgs = fill(h, [m("user", 10), m("system", 5), m("user", 10), m("user", 10)])
    assert h.messages() == [msgs[1], msgs[2], msgs[3]]
    assert h.total_tokens() == 25


def test_most_recent_is_kept_even_if_alone_it_exceeds_the_limit():
    h = History(limit=10)
    msgs = fill(h, [m("user", 5), m("user", 50)])
    assert h.messages() == [msgs[1]]
    assert h.total_tokens() == 50


def test_spec_example_tool_unit_dropped_together():
    h = History(limit=30)
    sys_ = m("system", 5)
    u1 = m("user", 10)
    a1 = m("assistant", 5, call_id="c1")
    t1 = m("tool", 5, call_id="c1")
    u2 = m("user", 10)
    fill(h, [sys_, u1, a1, t1, u2])
    assert h.messages() == [sys_, a1, t1, u2]
    assert h.total_tokens() == 25
    u3 = m("user", 10)
    h.append(u3)
    assert h.messages() == [sys_, u2, u3]
    assert h.total_tokens() == 25


def test_tool_result_never_survives_without_its_call():
    h = History(limit=12)
    a1 = m("assistant", 4, call_id="x")
    t1 = m("tool", 4, call_id="x")
    u = m("user", 5)
    fill(h, [a1, t1, u])
    assert h.messages() == [u]
    assert h.total_tokens() == 5


def test_multiple_tool_results_for_one_call_form_one_unit():
    h = History(limit=20)
    a1 = m("assistant", 3, call_id="k")
    t1 = m("tool", 3, call_id="k")
    t2 = m("tool", 3, call_id="k")
    u1 = m("user", 5)
    u2 = m("user", 8)
    fill(h, [a1, t1, t2, u1, u2])  # 22 > 20: drop the whole unit (9)
    assert h.messages() == [u1, u2]
    assert h.total_tokens() == 13


def test_unit_containing_the_most_recent_message_is_kept_whole():
    h = History(limit=10)
    u = m("user", 2)
    a1 = m("assistant", 6, call_id="z")
    t1 = m("tool", 6, call_id="z")
    fill(h, [u, a1, t1])
    assert h.messages() == [a1, t1]
    assert h.total_tokens() == 12


def test_assistant_without_call_id_is_a_single_message():
    h = History(limit=10)
    a = m("assistant", 6)
    u = m("user", 6)
    fill(h, [a, u])
    assert h.messages() == [u]


def test_total_tokens_tracks_drops():
    h = History(limit=10)
    for i in range(50):
        h.append(m("user", 3))
        assert h.total_tokens() == sum(x.tokens for x in h.messages())
        assert h.total_tokens() <= 10 or len(h.messages()) == 1


def test_two_hundred_thousand_appends_are_fast():
    h = History(limit=50_000)
    h.append(m("system", 1))
    for i in range(200_000):
        h.append(Message(id=str(i), role="user", text="", tokens=1))
    out = h.messages()
    assert out[0].role == "system"
    assert len(out) == 50_000
    assert out[-1].id == "199999"
    assert h.total_tokens() == 50_000
