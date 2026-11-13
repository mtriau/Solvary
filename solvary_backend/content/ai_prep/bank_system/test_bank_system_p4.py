# Provided tests for Level 4: merging accounts and balance history.
# Levels 1-3 still run against the same class.

import bank_system as bs


def two_accounts():
    bank = bs.Bank()
    bank.create_account(1, "alice")
    bank.create_account(2, "bob")
    bank.deposit(3, "alice", 100)
    bank.deposit(4, "bob", 40)
    return bank


def test_merge_sums_balances_into_the_first_account():
    bank = two_accounts()
    assert bank.merge_accounts(10, "alice", "bob") is True
    assert bank.deposit(11, "alice", 1) == 141


def test_merged_away_account_no_longer_exists():
    bank = two_accounts()
    bank.merge_accounts(10, "alice", "bob")
    assert bank.deposit(11, "bob", 1) is None
    assert bank.transfer(12, "alice", "bob", 1) is None
    assert bank.top_spenders(13, 5) == ["alice(0)"]
    assert bank.get_balance(14, "bob", 5) is None


def test_merge_with_unknown_or_same_account_returns_false():
    bank = two_accounts()
    assert bank.merge_accounts(10, "alice", "ghost") is False
    assert bank.merge_accounts(11, "ghost", "bob") is False
    assert bank.merge_accounts(12, "alice", "alice") is False
    assert bank.deposit(13, "bob", 1) == 41


def test_merge_adds_outgoing_totals_for_top_spenders():
    bank = two_accounts()
    bank.create_account(5, "carol")
    bank.transfer(6, "alice", "carol", 30)
    bank.transfer(7, "bob", "carol", 25)
    bank.transfer(8, "carol", "alice", 40)
    assert bank.top_spenders(9, 3) == ["carol(40)", "alice(30)", "bob(25)"]
    bank.merge_accounts(10, "bob", "alice")
    assert bank.top_spenders(11, 3) == ["bob(55)", "carol(40)"]


def test_reassigned_pending_payment_is_paid_from_the_survivor_balance():
    bank = two_accounts()
    pid = bank.schedule_payment(5, "bob", 120, 100)  # bob alone could not afford it
    bank.merge_accounts(6, "alice", "bob")
    assert bank.get_payment_status(7, "alice", pid) == "PENDING"
    assert bank.get_payment_status(200, "alice", pid) == "PAID"
    assert bank.deposit(201, "alice", 1) == 21
    assert bank.top_spenders(202, 1) == ["alice(120)"]


def test_reassigned_payment_belongs_to_the_survivor_only():
    bank = two_accounts()
    pid = bank.schedule_payment(5, "bob", 10, 100)
    bank.merge_accounts(6, "alice", "bob")
    assert bank.get_payment_status(7, "bob", pid) is None
    assert bank.cancel_payment(8, "bob", pid) is False
    assert bank.cancel_payment(9, "alice", pid) is True
    assert bank.get_payment_status(10, "alice", pid) == "CANCELED"


def test_payment_due_at_the_merge_timestamp_runs_before_the_merge():
    bank = two_accounts()
    pid = bank.schedule_payment(5, "bob", 30, 5)  # due 10, from bob's 40
    bank.merge_accounts(10, "alice", "bob")
    assert bank.get_payment_status(11, "alice", pid) == "PAID"
    assert bank.deposit(12, "alice", 1) == 111  # 100 + (40 - 30) + 1


def test_get_balance_is_none_before_the_account_existed():
    bank = bs.Bank()
    bank.create_account(10, "alice")
    bank.deposit(20, "alice", 5)
    assert bank.get_balance(30, "alice", 9) is None
    assert bank.get_balance(31, "alice", 10) == 0
    assert bank.get_balance(32, "ghost", 10) is None


def test_get_balance_between_operations_returns_the_earlier_checkpoint():
    bank = bs.Bank()
    bank.create_account(1, "alice")
    bank.create_account(2, "bob")
    bank.deposit(10, "alice", 100)
    bank.transfer(20, "alice", "bob", 30)
    bank.deposit(30, "alice", 5)
    assert bank.get_balance(40, "alice", 15) == 100
    assert bank.get_balance(41, "alice", 25) == 70
    assert bank.get_balance(42, "bob", 25) == 30
    assert bank.get_balance(43, "bob", 5) == 0


def test_get_balance_includes_operations_at_exactly_time_at():
    bank = bs.Bank()
    bank.create_account(1, "alice")
    bank.deposit(10, "alice", 100)
    bank.deposit(20, "alice", 1)
    assert bank.get_balance(30, "alice", 10) == 100
    assert bank.get_balance(31, "alice", 20) == 101
    assert bank.get_balance(32, "alice", 30) == 101


def test_get_balance_sees_scheduled_payment_at_its_due_time():
    bank = bs.Bank()
    bank.create_account(1, "alice")
    bank.deposit(2, "alice", 100)
    bank.schedule_payment(3, "alice", 40, 10)  # due 13
    assert bank.get_balance(50, "alice", 12) == 100
    assert bank.get_balance(51, "alice", 13) == 60


def test_history_after_merge_includes_merged_balance_from_merge_time():
    bank = two_accounts()
    bank.deposit(8, "alice", 10)
    bank.merge_accounts(10, "alice", "bob")
    bank.deposit(20, "alice", 1)
    assert bank.get_balance(30, "alice", 9) == 110  # before the merge: alice alone
    assert bank.get_balance(31, "alice", 10) == 150  # from the merge on: 110 + 40
    assert bank.get_balance(32, "alice", 19) == 150
    assert bank.get_balance(33, "alice", 20) == 151


