from dig import dig

CFG = {"db": {"hosts": ["a", "b"], "port": 5432}, "flag": None}


def test_dict_path():
    assert dig(CFG, "db", "port") == 5432


def test_through_a_list_index():
    assert dig(CFG, "db", "hosts", 1) == "b"


def test_missing_key_gives_default():
    assert dig(CFG, "db", "user") is None
    assert dig(CFG, "db", "user", default="?") == "?"


def test_bad_index_gives_default():
    assert dig(CFG, "db", "hosts", 9, default="?") == "?"


def test_not_subscriptable_gives_default():
    assert dig(CFG, "db", "port", "x") is None


def test_empty_path_returns_data():
    assert dig(CFG) is CFG


def test_existing_none_value_is_returned_not_default():
    assert dig(CFG, "flag", default="d") is None
