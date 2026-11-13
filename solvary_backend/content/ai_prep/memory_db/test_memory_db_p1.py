# Provided tests for Part 1: SET, GET, DELETE.

import memory_db


def make():
    return memory_db.MemoryDB()


def test_get_returns_the_value_that_was_set():
    db = make()
    db.set("user:1", "name", "Ada")
    assert db.get("user:1", "name") == "Ada"


def test_get_unknown_key_returns_none():
    assert make().get("nope", "name") is None


def test_get_unknown_field_of_known_key_returns_none():
    db = make()
    db.set("user:1", "name", "Ada")
    assert db.get("user:1", "email") is None


def test_set_overwrites_the_previous_value():
    db = make()
    db.set("k", "f", "old")
    db.set("k", "f", "new")
    assert db.get("k", "f") == "new"


def test_fields_of_one_record_are_independent():
    db = make()
    db.set("k", "a", "1")
    db.set("k", "b", "2")
    db.set("k", "a", "3")
    assert db.get("k", "a") == "3"
    assert db.get("k", "b") == "2"


def test_records_are_independent():
    db = make()
    db.set("k1", "f", "one")
    db.set("k2", "f", "two")
    assert db.get("k1", "f") == "one"
    assert db.get("k2", "f") == "two"


def test_delete_existing_field_returns_true_and_removes_it():
    db = make()
    db.set("k", "f", "v")
    assert db.delete("k", "f") is True
    assert db.get("k", "f") is None


def test_delete_missing_field_or_key_returns_false():
    db = make()
    db.set("k", "f", "v")
    assert db.delete("k", "other") is False
    assert db.delete("nope", "f") is False
    assert db.get("k", "f") == "v"


def test_delete_twice_returns_false_the_second_time():
    db = make()
    db.set("k", "f", "v")
    assert db.delete("k", "f") is True
    assert db.delete("k", "f") is False


def test_delete_leaves_other_fields_alone():
    db = make()
    db.set("k", "a", "1")
    db.set("k", "b", "2")
    db.delete("k", "a")
    assert db.get("k", "b") == "2"


def test_a_field_can_be_set_again_after_delete():
    db = make()
    db.set("k", "f", "v1")
    db.delete("k", "f")
    db.set("k", "f", "v2")
    assert db.get("k", "f") == "v2"


def test_empty_string_is_a_real_value_not_none():
    db = make()
    db.set("k", "f", "")
    assert db.get("k", "f") == ""
    assert db.delete("k", "f") is True
