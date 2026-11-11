from flatten_dict import flatten


def test_example():
    assert flatten({"a": {"b": 1, "c": {"d": 2}}, "e": 3}) == {"a.b": 1, "a.c.d": 2, "e": 3}


def test_empty():
    assert flatten({}) == {}


def test_already_flat():
    assert flatten({"x": 1, "y": 2}) == {"x": 1, "y": 2}


def test_empty_nested_dict_contributes_nothing():
    assert flatten({"a": {}, "b": 1}) == {"b": 1}


def test_lists_are_leaves():
    assert flatten({"a": {"b": [1, 2]}}) == {"a.b": [1, 2]}


def test_none_and_falsy_values_are_kept():
    assert flatten({"a": {"b": None, "c": 0, "d": ""}}) == {"a.b": None, "a.c": 0, "a.d": ""}


def test_deep_nesting():
    d = {"k": 1}
    for name in "edcba":
        d = {name: d}
    assert flatten(d) == {"a.b.c.d.e.k": 1}
