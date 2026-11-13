# Provided tests for Level 1: accounts, deposits, transfers.

import bank_system as bs


def funded(**balances):
    """A bank whose accounts hold the given balances (setup uses timestamps 1..)."""
    bank = bs.Bank()
    t = 1
    for name, amount in balances.items():
        assert bank.create_account(t, name) is True
        t += 1
        if amount:
            bank.deposit(t, name, amount)
            t += 1
    return bank, t


def test_create_account_returns_true_for_new_account():
    assert bs.Bank().create_account(1, "alice") is True


def test_create_account_returns_false_for_duplicate():
    bank = bs.Bank()
    bank.create_account(1, "alice")
    assert bank.create_account(2, "alice") is False


def test_deposit_returns_new_balance_and_accumulates():
    bank = bs.Bank()
    bank.create_account(1, "alice")
    assert bank.deposit(2, "alice", 100) == 100
    assert bank.deposit(3, "alice", 50) == 150


def test_deposit_to_unknown_account_returns_none():
    assert bs.Bank().deposit(1, "ghost", 10) is None


def test_deposit_does_not_create_the_account():
    bank = bs.Bank()
    assert bank.deposit(1, "ghost", 10) is None
    assert bank.create_account(2, "ghost") is True
    assert bank.deposit(3, "ghost", 5) == 5


def test_transfer_moves_money_and_returns_source_balance():
    bank, t = funded(alice=100, bob=0)
    assert bank.transfer(t, "alice", "bob", 30) == 70
    assert bank.deposit(t + 1, "bob", 1) == 31


def test_transfer_of_entire_balance_leaves_zero():
    bank, t = funded(alice=40, bob=5)
    assert bank.transfer(t, "alice", "bob", 40) == 0


def test_transfer_with_insufficient_funds_returns_none_and_changes_nothing():
    bank, t = funded(alice=10, bob=0)
    assert bank.transfer(t, "alice", "bob", 11) is None
    assert bank.deposit(t + 1, "alice", 1) == 11
    assert bank.deposit(t + 2, "bob", 1) == 1


def test_transfer_with_unknown_account_returns_none_and_does_not_debit():
    bank, t = funded(alice=50)
    assert bank.transfer(t, "alice", "ghost", 10) is None
    assert bank.transfer(t + 1, "ghost", "alice", 10) is None
    assert bank.deposit(t + 2, "alice", 1) == 51


def test_transfer_to_self_returns_none():
    bank, t = funded(alice=50)
    assert bank.transfer(t, "alice", "alice", 10) is None
    assert bank.deposit(t + 1, "alice", 1) == 51


def test_two_banks_do_not_share_state():
    one, two = bs.Bank(), bs.Bank()
    one.create_account(1, "alice")
    assert two.create_account(1, "alice") is True
    assert two.deposit(2, "alice", 5) == 5
    assert one.deposit(2, "alice", 7) == 7
