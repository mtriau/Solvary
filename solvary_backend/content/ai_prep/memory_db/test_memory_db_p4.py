# Provided tests for Part 4: BACKUP and RESTORE.

import memory_db


def make():
    return memory_db.MemoryDB()


def test_backup_returns_number_of_records():
    db = make()
    db.set_at("a", "f", "1", 1)
    db.set_at("a", "g", "2", 2)
    db.set_at("b", "f", "3", 3)
    assert db.backup(4) == 2


def test_backup_counts_a_record_with_one_live_field_among_expired_ones():
    db = make()
    db.set_at_with_ttl("a", "f", "1", 1, 2)
    db.set_at("a", "g", "2", 2)
    assert db.backup(10) == 1


def test_backup_excludes_records_whose_fields_have_all_expired():
    db = make()
    db.set_at_with_ttl("a", "f", "1", 1, 5)   # expires at 6
    db.set_at("b", "f", "2", 2)
    assert db.backup(5) == 2
    assert db.backup(6) == 1


def test_restore_brings_back_state_at_backup_time():
    db = make()
    db.set_at("k", "a", "1", 1)
    db.backup(2)
    db.set_at("k", "a", "changed", 3)
    db.set_at("k", "b", "new", 4)
    db.restore(5, 2)
    assert db.get_at("k", "a", 6) == "1"
    assert db.get_at("k", "b", 7) is None
    assert db.scan_at("k", 8) == ["a(1)"]


def test_restore_recomputes_ttl_from_remaining_lifetime():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 10, 10)  # expires at 20
    db.backup(13)                              # 7 seconds left
    db.restore(100, 13)                        # now expires at 107
    assert db.get_at("k", "f", 106) == "v"
    assert db.get_at("k", "f", 107) is None


def test_restore_ttl_field_is_alive_6_after_restore_and_gone_7_after():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 10, 10)
    db.backup(13)
    db.restore(50, 13)
    assert db.get_at("k", "f", 56) == "v"
    assert db.get_at("k", "f", 57) is None


def test_restore_does_not_resurrect_fields_that_expired_before_the_backup():
    db = make()
    db.set_at_with_ttl("k", "gone", "x", 1, 2)
    db.set_at("k", "kept", "y", 2)
    db.backup(10)
    db.restore(11, 10)
    assert db.scan_at("k", 12) == ["kept(y)"]


def test_restore_with_no_backup_at_or_before_the_time_is_a_no_op():
    db = make()
    db.set_at("k", "f", "v", 1)
    db.backup(5)
    db.set_at("k", "g", "w", 6)
    db.restore(7, 4)  # the only backup is at 5, after 4
    assert db.scan_at("k", 8) == ["f(v)", "g(w)"]


def test_restore_picks_the_latest_backup_at_or_before_the_requested_time():
    db = make()
    db.set_at("k", "f", "one", 1)
    db.backup(2)
    db.set_at("k", "f", "two", 3)
    db.backup(4)
    db.set_at("k", "f", "three", 5)
    db.backup(6)
    db.restore(7, 5)
    assert db.get_at("k", "f", 8) == "two"


def test_restore_uses_a_backup_taken_exactly_at_the_requested_time():
    db = make()
    db.set_at("k", "f", "one", 1)
    db.backup(2)
    db.set_at("k", "f", "two", 3)
    db.restore(4, 2)
    assert db.get_at("k", "f", 5) == "one"


def test_operations_after_restore_see_and_build_on_the_restored_state():
    db = make()
    db.set_at("k", "a", "1", 1)
    db.backup(2)
    db.set_at("k", "a", "2", 3)
    db.restore(4, 2)
    db.set_at("k", "b", "x", 5)
    assert db.delete_at("k", "a", 6) is True
    assert db.scan_at("k", 7) == ["b(x)"]


def test_plain_methods_work_on_the_restored_state():
    db = make()
    db.set("k", "a", "1")
    db.backup(1)
    db.set("k", "a", "2")
    db.restore(2, 1)
    assert db.get("k", "a") == "1"
    assert db.scan("k") == ["a(1)"]


def test_a_second_backup_after_restore_captures_the_restored_state():
    db = make()
    db.set_at_with_ttl("k", "f", "v", 10, 10)  # expires at 20
    db.backup(13)                              # 7 left
    db.set_at("other", "x", "y", 14)
    db.restore(50, 13)                         # f expires at 57, other gone
    assert db.backup(52) == 1                  # 5 left
    db.restore(100, 52)                        # f expires at 105
    assert db.get_at("k", "f", 104) == "v"
    assert db.get_at("k", "f", 105) is None


def test_backups_taken_before_a_restore_stay_available_afterwards():
    db = make()
    db.set_at("k", "f", "one", 1)
    db.backup(2)
    db.set_at("k", "f", "two", 3)
    db.backup(4)
    db.restore(5, 2)
    assert db.get_at("k", "f", 6) == "one"
    db.restore(7, 4)
    assert db.get_at("k", "f", 8) == "two"


def test_restored_ttl_also_drives_the_next_backup_count():
    db = make()
    db.set_at_with_ttl("a", "f", "1", 1, 10)  # expires at 11, 9 left at backup(2)
    db.backup(2)
    db.restore(10, 2)                         # f now expires at 19
    assert db.backup(18) == 1
    assert db.backup(19) == 0
