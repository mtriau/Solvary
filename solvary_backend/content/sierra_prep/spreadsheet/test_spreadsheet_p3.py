# Provided tests for Part 3: deep chains, diamonds, dependents, evaluation order.

from spreadsheet import Sheet


def test_spec_example():
    s = Sheet()
    s.set("A1", 1)
    s.set("A2", "=A1+1")
    s.set("A3", "=A2+A1")
    s.set("Z1", 7)
    assert s.dependents("A1") == {"A2", "A3"}
    assert s.dependents("Z1") == set()
    order = s.evaluation_order()
    assert sorted(order) == ["A1", "A2", "A3", "Z1"]
    assert order.index("A1") < order.index("A2") < order.index("A3")


def test_deep_chain_does_not_hit_the_recursion_limit():
    s = Sheet()
    s.set("A0", 0)
    for i in range(1, 1501):
        s.set(f"A{i}", f"=A{i - 1}+1")
    assert s.get("A1500") == 1500


def test_doubling_diamond_is_not_exponential():
    s = Sheet()
    s.set("B0", 1)
    for i in range(1, 61):
        s.set(f"B{i}", f"=B{i - 1}+B{i - 1}")
    assert s.get("B60") == 2**60


def test_dependents_transitive_and_excludes_self():
    s = Sheet()
    s.set("A1", 1)
    s.set("B1", "=A1")
    s.set("C1", "=B1")
    s.set("D1", "=A1+C1")
    s.set("E1", 5)
    assert s.dependents("A1") == {"B1", "C1", "D1"}
    assert s.dependents("B1") == {"C1", "D1"}
    assert s.dependents("D1") == set()
    assert s.dependents("E1") == set()


def test_dependents_of_unset_referenced_cell():
    s = Sheet()
    s.set("A1", "=X1+1")
    s.set("B1", "=A1")
    assert s.dependents("X1") == {"A1", "B1"}
    assert s.dependents("NOPE") == set()


def test_dependents_reflect_updates():
    s = Sheet()
    s.set("A1", 1)
    s.set("B1", "=A1")
    assert s.dependents("A1") == {"B1"}
    s.set("B1", 2)
    assert s.dependents("A1") == set()


def test_evaluation_order_respects_every_edge():
    s = Sheet()
    s.set("A1", 1)
    s.set("B1", "=A1")
    s.set("C1", "=A1")
    s.set("D1", "=B1+C1")
    s.set("E1", "=D1+X1")  # X1 is unset
    s.set("F1", 3)
    order = s.evaluation_order()
    assert sorted(order) == ["A1", "B1", "C1", "D1", "E1", "F1"]
    pos = {c: i for i, c in enumerate(order)}
    for cell in order:
        for r in s.refs(cell):
            if r in pos:
                assert pos[r] < pos[cell], (r, cell)


def test_evaluation_order_empty_sheet():
    assert Sheet().evaluation_order() == []


def test_evaluation_order_on_deep_chain():
    s = Sheet()
    s.set("A0", 0)
    for i in range(1, 1201):
        s.set(f"A{i}", f"=A{i - 1}")
    order = s.evaluation_order()
    assert len(order) == 1201
    assert order[0] == "A0" and order[-1] == "A1200"
