from merge_settings import merge_settings


def test_example():
    assert merge_settings({"theme": "light", "font": 12}, {"theme": "dark", "font": None}) == {
        "theme": "dark",
        "font": 12,
    }


def test_new_keys_are_added():
    assert merge_settings({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_none_override_keeps_default():
    assert merge_settings({"a": 1}, {"a": None}) == {"a": 1}


def test_falsy_but_not_none_overrides():
    assert merge_settings({"a": 1, "b": "x"}, {"a": 0, "b": ""}) == {"a": 0, "b": ""}


def test_inputs_are_not_mutated():
    defaults = {"a": 1}
    overrides = {"a": 2, "c": None}
    merge_settings(defaults, overrides)
    assert defaults == {"a": 1}
    assert overrides == {"a": 2, "c": None}


def test_empty_overrides():
    assert merge_settings({"a": 1}, {}) == {"a": 1}
