from parse_pairs import parse_pairs


def test_example():
    assert parse_pairs("a=1;b=22;c=3") == {"a": 1, "b": 22, "c": 3}


def test_whitespace_is_ignored():
    assert parse_pairs(" a = 1 ; b=2 ") == {"a": 1, "b": 2}


def test_empty_items_are_skipped():
    assert parse_pairs("a=1;;b=2;") == {"a": 1, "b": 2}


def test_empty_string():
    assert parse_pairs("") == {}


def test_values_are_ints():
    assert parse_pairs("n=-5") == {"n": -5}
    assert type(parse_pairs("n=5")["n"]) is int


def test_later_key_wins():
    assert parse_pairs("a=1;a=2") == {"a": 2}
