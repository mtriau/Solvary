from has_cycle import has_cycle


def test_chain_has_no_cycle():
    assert has_cycle({"a": {"b"}, "b": {"c"}, "c": set()}) is False


def test_two_node_cycle():
    assert has_cycle({"a": {"b"}, "b": {"a"}}) is True


def test_self_loop():
    assert has_cycle({"a": {"a"}}) is True


def test_empty():
    assert has_cycle({}) is False


def test_diamond_is_not_a_cycle():
    g = {"a": {"b", "c"}, "b": {"d"}, "c": {"d"}, "d": set()}
    assert has_cycle(g) is False


def test_cycle_not_reachable_from_the_first_node():
    g = {"a": {"b"}, "b": set(), "x": {"y"}, "y": {"x"}}
    assert has_cycle(g) is True


def test_long_chain_then_cycle_at_the_end():
    n = 4000
    g = {str(i): {str(i + 1)} for i in range(n)}
    g[str(n)] = {str(n // 2)}
    assert has_cycle(g) is True


def test_long_chain_without_cycle():
    n = 4000
    g = {str(i): {str(i + 1)} for i in range(n)}
    g[str(n)] = set()
    assert has_cycle(g) is False
