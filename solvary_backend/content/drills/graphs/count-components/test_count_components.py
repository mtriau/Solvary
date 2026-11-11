from count_components import count_components


def test_example():
    assert count_components({"a": {"b"}, "b": {"a"}, "c": set()}) == 2


def test_empty():
    assert count_components({}) == 0


def test_all_isolated():
    assert count_components({"a": set(), "b": set(), "c": set()}) == 3


def test_single_component_with_cycle():
    g = {"a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"}}
    assert count_components(g) == 1


def test_two_triangles():
    g = {
        "a": {"b", "c"}, "b": {"a", "c"}, "c": {"a", "b"},
        "x": {"y", "z"}, "y": {"x", "z"}, "z": {"x", "y"},
    }
    assert count_components(g) == 2


def test_long_chain_does_not_hit_the_recursion_limit():
    n = 5000
    g = {str(i): set() for i in range(n)}
    for i in range(n - 1):
        g[str(i)].add(str(i + 1))
        g[str(i + 1)].add(str(i))
    assert count_components(g) == 1
