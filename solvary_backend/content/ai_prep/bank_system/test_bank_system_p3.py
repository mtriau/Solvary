# Provided tests for Level 3: scheduled payments.
# Levels 1 and 2 still run against the same class.

import bank_system as bs


def bank_with(balance=100):
    bank = bs.Bank()
    bank.create_account(1, "alice")
    bank.create_account(2, "bob")
    bank.deposit(3, "alice", balance)
    return bank


def test_payment_ids_count_up_globally():
    bank = bank_with()
    assert bank.schedule_payment(4, "alice", 10, 100) == "payment1"
    assert bank.schedule_payment(5, "bob", 10, 100) == "payment2"
    assert bank.schedule_payment(6, "alice", 10, 100) == "payment3"
    assert bank.schedule_payment(7, "ghost", 10, 5) is None  # no id consumed
    assert bank.schedule_payment(8, "alice", 10, 100) == "payment4"


def test_payment_is_pending_until_due_then_paid():
    bank = bank_with()
    pid = bank.schedule_payment(10, "alice", 30, 10)
    assert bank.get_payment_status(19, "alice", pid) == "PENDING"
    assert bank.deposit(19, "alice", 1) == 101  # nothing taken yet
    assert bank.get_payment_status(25, "alice", pid) == "PAID"
    assert bank.deposit(26, "alice", 1) == 72


def test_payment_due_exactly_at_a_later_timestamp_runs_before_that_operation():
    bank = bank_with(100)
    bank.schedule_payment(5, "alice", 80, 10)  # due at 15
    assert bank.transfer(15, "alice", "bob", 50) is None  # only 20 left by then
    assert bank.deposit(16, "alice", 1) == 21


def test_payment_due_before_a_later_operation_runs_before_it():
    bank = bank_with(100)
    bank.schedule_payment(5, "alice", 60, 10)  # due at 15
    assert bank.deposit(500, "alice", 5) == 45


def test_due_payments_run_in_scheduling_order_and_second_can_fail():
    bank = bank_with(100)
    first = bank.schedule_payment(5, "alice", 70, 10)  # due 15
    second = bank.schedule_payment(6, "alice", 70, 9)  # due 15 as well
    assert bank.get_payment_status(40, "alice", first) == "PAID"
    assert bank.get_payment_status(41, "alice", second) == "FAILED"
    assert bank.deposit(42, "alice", 1) == 31


def test_failed_payment_stays_failed_after_a_later_deposit():
    bank = bank_with(10)
    pid = bank.schedule_payment(5, "alice", 50, 5)
    assert bank.deposit(11, "alice", 1000) == 1010
    assert bank.get_payment_status(12, "alice", pid) == "FAILED"
    assert bank.deposit(13, "alice", 1) == 1011


def test_canceled_payment_is_not_paid():
    bank = bank_with(100)
    pid = bank.schedule_payment(5, "alice", 60, 10)
    assert bank.cancel_payment(6, "alice", pid) is True
    assert bank.get_payment_status(7, "alice", pid) == "CANCELED"
    assert bank.deposit(100, "alice", 1) == 101
    assert bank.get_payment_status(101, "alice", pid) == "CANCELED"


def test_cancel_by_another_account_returns_false():
    bank = bank_with(100)
    pid = bank.schedule_payment(5, "alice", 60, 10)
    assert bank.cancel_payment(6, "bob", pid) is False
    assert bank.get_payment_status(7, "alice", pid) == "PENDING"


def test_cancel_unknown_twice_or_after_payment_returns_false():
    bank = bank_with(100)
    pid = bank.schedule_payment(5, "alice", 10, 10)
    other = bank.schedule_payment(6, "alice", 10, 100)
    assert bank.cancel_payment(7, "alice", "payment99") is False
    assert bank.cancel_payment(8, "alice", other) is True
    assert bank.cancel_payment(9, "alice", other) is False
    assert bank.cancel_payment(20, "alice", pid) is False  # already PAID


def test_cancel_at_the_due_timestamp_is_too_late():
    bank = bank_with(100)
    pid = bank.schedule_payment(5, "alice", 10, 10)  # due 15
    assert bank.cancel_payment(15, "alice", pid) is False
    assert bank.get_payment_status(16, "alice", pid) == "PAID"


def test_status_is_none_for_unknown_payment_or_wrong_account():
    bank = bank_with()
    pid = bank.schedule_payment(4, "alice", 10, 10)
    assert bank.get_payment_status(5, "alice", "payment42") is None
    assert bank.get_payment_status(6, "bob", pid) is None


def test_only_paid_payments_count_toward_top_spenders():
    bank = bank_with(100)
    bank.schedule_payment(4, "alice", 30, 5)  # due 9, paid
    bank.schedule_payment(5, "bob", 25, 5)  # due 10, bob holds only 20: fails
    bank.transfer(6, "alice", "bob", 20)
    bank.schedule_payment(7, "alice", 10, 100)  # still pending
    canceled = bank.schedule_payment(8, "alice", 10, 1)
    bank.cancel_payment(8, "alice", canceled)
    assert bank.top_spenders(8, 2) == ["alice(20)", "bob(0)"]
    assert bank.top_spenders(20, 2) == ["alice(50)", "bob(0)"]
