from adjacency import adjacency


def test_example():
    assert adjacency([("a", "b"), ("b", "c")]) == {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}


def test_isolated_node_present():
    assert adjacency([], nodes=["x"]) == {"x": set()}


def test_empty():
    assert adjacency([]) == {}


def test_duplicate_edges_collapse():
    assert adjacency([("a", "b"), ("b", "a"), ("a", "b")]) == {"a": {"b"}, "b": {"a"}}


def test_self_loop():
    assert adjacency([("a", "a")]) == {"a": {"a"}}


def test_returns_a_plain_dict_without_default_behaviour():
    g = adjacency([("a", "b")])
    assert type(g) is dict
    assert "zzz" not in g
