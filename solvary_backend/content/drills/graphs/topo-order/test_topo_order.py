import pytest
from topo_order import topo_order


def _valid(order, deps):
    pos = {t: i for i, t in enumerate(order)}
    return sorted(order) == sorted(deps) and all(
        pos[need] < pos[task] for task, needs in deps.items() for need in needs
    )


def test_chain():
    deps = {"build": {"compile"}, "compile": {"fetch"}, "fetch": set()}
    assert topo_order(deps) == ["fetch", "compile", "build"]


def test_cycle_raises():
    with pytest.raises(ValueError):
        topo_order({"a": {"b"}, "b": {"a"}})


def test_self_dependency_raises():
    with pytest.raises(ValueError):
        topo_order({"a": {"a"}})


def test_empty():
    assert topo_order({}) == []


def test_diamond_any_valid_order():
    deps = {"d": {"b", "c"}, "b": {"a"}, "c": {"a"}, "a": set()}
    order = topo_order(deps)
    assert _valid(order, deps)
    assert order[0] == "a" and order[-1] == "d"


def test_independent_tasks_all_present():
    deps = {"x": set(), "y": set(), "z": set()}
    assert sorted(topo_order(deps)) == ["x", "y", "z"]


def test_long_chain():
    n = 3000
    deps = {str(i): {str(i - 1)} for i in range(1, n)}
    deps["0"] = set()
    order = topo_order(deps)
    assert _valid(order, deps)
