# Provided tests for Part 1: numbers, additive formulas, lazy evaluation.

from spreadsheet import Sheet


def test_spec_example():
    s = Sheet()
    s.set("A1", 5)
    s.set("A2", "=A1 + 10")
    s.set("A3", "=A1+A2+A1")
    assert s.get("A3") == 25
    assert s.refs("A3") == ["A1", "A2"]
    s.set("A1", 1)
    assert s.get("A3") == 13
    assert s.get("Z9") == 0


def test_number_cell():
    s = Sheet()
    s.set("B2", 42)
    assert s.get("B2") == 42
    assert s.refs("B2") == []


def test_unset_cell_is_zero_with_no_refs():
    s = Sheet()
    assert s.get("Q1") == 0
    assert s.refs("Q1") == []


def test_formula_of_constants_only():
    s = Sheet()
    s.set("A1", "=1+2+3")
    assert s.get("A1") == 6
    assert s.refs("A1") == []


def test_formula_referencing_unset_cell_counts_zero():
    s = Sheet()
    s.set("A1", "=B1+4")
    assert s.get("A1") == 4
    s.set("B1", 6)
    assert s.get("A1") == 10


def test_multi_letter_and_multi_digit_names():
    s = Sheet()
    s.set("AB12", 3)
    s.set("C100", "=AB12+AB12")
    assert s.get("C100") == 6
    assert s.refs("C100") == ["AB12"]


def test_spaces_are_tolerated():
    s = Sheet()
    s.set("A1", 2)
    s.set("A2", "= A1 +  3 + A1 ")
    assert s.get("A2") == 7
    assert s.refs("A2") == ["A1"]


def test_refs_order_of_first_appearance():
    s = Sheet()
    s.set("A1", "=C1+B1+C1+A2+B1")
    assert s.refs("A1") == ["C1", "B1", "A2"]


def test_chain_evaluates_transitively():
    s = Sheet()
    s.set("A1", 1)
    s.set("A2", "=A1+1")
    s.set("A3", "=A2+1")
    s.set("A4", "=A3+1")
    assert s.get("A4") == 4


def test_replacing_a_formula_with_a_number():
    s = Sheet()
    s.set("A1", 1)
    s.set("A2", "=A1+1")
    s.set("A2", 100)
    assert s.get("A2") == 100
    assert s.refs("A2") == []


def test_lazy_reads_reflect_later_changes_down_the_chain():
    s = Sheet()
    s.set("T1", "=A1+B1")
    s.set("A1", "=C1")
    s.set("B1", 1)
    assert s.get("T1") == 1
    s.set("C1", 41)
    assert s.get("T1") == 42
