# Provided tests for Level 2: top spenders.

import bank_system as bs


def funded(**balances):
    bank = bs.Bank()
    t = 1
    for name, amount in balances.items():
        bank.create_account(t, name)
        t += 1
        if amount:
            bank.deposit(t, name, amount)
            t += 1
    return bank, t


def test_no_accounts_gives_empty_list():
    assert bs.Bank().top_spenders(1, 3) == []


def test_accounts_that_never_spent_show_zero():
    bank, t = funded(alice=10, bob=0)
    assert bank.top_spenders(t, 5) == ["alice(0)", "bob(0)"]


def test_sorted_by_outgoing_descending():
    bank, t = funded(a=100, b=100, c=100)
    bank.transfer(t, "a", "c", 10)
    bank.transfer(t + 1, "b", "c", 40)
    bank.transfer(t + 2, "c", "a", 25)
    assert bank.top_spenders(t + 3, 3) == ["b(40)", "c(25)", "a(10)"]


def test_ties_break_by_account_id_ascending():
    bank, t = funded(zed=50, amy=50, bob=50, sink=0)
    for i, name in enumerate(["zed", "amy", "bob"]):
        bank.transfer(t + i, name, "sink", 20)
    assert bank.top_spenders(t + 3, 4) == ["amy(20)", "bob(20)", "zed(20)", "sink(0)"]


def test_n_limits_the_result():
    bank, t = funded(a=100, b=100, c=100)
    bank.transfer(t, "a", "b", 1)
    bank.transfer(t + 1, "b", "c", 5)
    assert bank.top_spenders(t + 2, 1) == ["b(5)"]
    assert bank.top_spenders(t + 3, 2) == ["b(5)", "a(1)"]


def test_n_larger_than_account_count_returns_all():
    bank, t = funded(a=1, b=1)
    assert len(bank.top_spenders(t, 10)) == 2


def test_n_zero_returns_empty_list():
    bank, t = funded(a=1)
    assert bank.top_spenders(t, 0) == []


def test_repeated_transfers_accumulate():
    bank, t = funded(a=100, b=0)
    bank.transfer(t, "a", "b", 10)
    bank.transfer(t + 1, "a", "b", 15)
    assert bank.top_spenders(t + 2, 1) == ["a(25)"]


def test_deposits_and_incoming_transfers_do_not_count():
    bank, t = funded(a=100, b=0)
    bank.transfer(t, "a", "b", 60)
    assert bank.top_spenders(t + 1, 2) == ["a(60)", "b(0)"]


def test_failed_transfers_do_not_count():
    bank, t = funded(a=10, b=0)
    assert bank.transfer(t, "a", "b", 50) is None
    assert bank.transfer(t + 1, "a", "ghost", 5) is None
    assert bank.transfer(t + 2, "a", "a", 5) is None
    assert bank.top_spenders(t + 3, 2) == ["a(0)", "b(0)"]
