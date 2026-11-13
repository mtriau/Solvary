# Banking System: Part 4

The same `Bank` class grows one last time: accounts can be merged, and the
bank can answer questions about the past. The Level 1-3 tests still run.

### What to implement

- `merge_accounts(timestamp, account_id_1, account_id_2) -> bool`: account 1
  **absorbs** account 2. Return `False` (changing nothing) if either account
  is unknown or they are the same account; otherwise `True`.
- `get_balance(timestamp, account_id, time_at) -> int | None`: the balance
  `account_id` had **right after all operations at or before `time_at` were
  applied**. `None` if the account did not exist at `time_at`.

### Rules

- On a merge, account 1's balance becomes the sum of both balances, and its
  total outgoing becomes the sum of both totals (so `top_spenders` sees the
  combined figure).
- Account 2's payments (pending ones execute later) move to account 1: they
  now belong to account 1 for `cancel_payment` and `get_payment_status`, and a
  pending one is paid from account 1's balance. Asking about them under
  account 2's id returns `False` / `None`.
- Account 2 ceases to exist: later operations on it behave as for an unknown
  account, and `get_balance` for it returns `None` for any `time_at`.
- As always, payments due at or before the merge timestamp run first, so a
  payment of account 2 due at the merge time is paid from account 2's own
  balance.
- Balance history: a surviving account's history before the merge is its own
  history; from the merge timestamp on, it includes the absorbed balance.
  A payment's balance change is recorded at its execute time, not at the
  timestamp of the operation that happened to settle it.

### Worked example

```python
bank = Bank()
bank.create_account(1, "alice")
bank.create_account(2, "bob")
bank.deposit(3, "alice", 100)
bank.deposit(4, "bob", 40)
bank.get_balance(5, "alice", 3)            # -> 100
bank.get_balance(6, "alice", 2)            # -> 0  (existed since time 1)
bank.merge_accounts(10, "alice", "bob")    # -> True
bank.get_balance(11, "alice", 9)           # -> 100 (before the merge)
bank.get_balance(12, "alice", 10)          # -> 140 (from the merge on)
bank.get_balance(13, "bob", 4)             # -> None (bob no longer exists)
```

### Clarifications

- **What is the balance of an account at a time before it was created?**
  `None`. At its creation time it is `0`.
- **`time_at` falls between two operations?** The earlier checkpoint's
  balance. Nothing changed in between.
- **Is `time_at` ever later than `timestamp`?** No; the tests ask about the
  past or the present.
- **What happens to account 2's already-paid or failed payments?** They move
  with the rest of its payments, so the survivor can still look up their
  status.
- **Can I reuse a merged-away id?** Not exercised by the tests.

Run the provided tests with **Submit**; earlier levels still run too.

---
Interviewer notes

Graders look for per-account balance history stored as ordered `(timestamp, balance)` checkpoints and answered with `bisect`, rather than replaying a global log on every query. Candidates stall on merge details: moving payments, adding outgoing totals, and writing a checkpoint at the merge time so the combined balance shows up in history. If they reached Level 3 with processing in one helper, this level is a small extension; if not, expect a rewrite.
