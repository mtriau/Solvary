# Banking System: Part 1

This mirrors the CodeSignal four-level coding assessment used for banking-system
questions: 90 minutes, one `Bank` class that grows level by level, and the next
level unlocks only when the current suite is green. Three clean levels beat four
broken ones, so keep the data model simple and readable, because Levels 3 and 4
will lean on it. Every operation takes a strictly increasing integer
`timestamp` as its first argument. Level 1 does not need it yet; keep it anyway.

### What to implement

In `bank_system.py`, a class `Bank` with:

- `create_account(timestamp, account_id) -> bool`: `True` if the account was
  created, `False` if `account_id` already exists.
- `deposit(timestamp, account_id, amount) -> int | None`: add `amount` and
  return the **new balance**; `None` if the account does not exist.
- `transfer(timestamp, source, target, amount) -> int | None`: move `amount`
  from `source` to `target` and return the **source's new balance**. Return
  `None` (and change nothing) if either account is unknown, if
  `source == target`, or if the source balance is less than `amount`.

### Rules

- Accounts start with a balance of `0`. Account ids are strings.
- Amounts are positive integers.
- A failed operation never changes any balance.

### Worked example

```python
bank = Bank()
bank.create_account(1, "alice")      # -> True
bank.create_account(2, "alice")      # -> False
bank.create_account(3, "bob")        # -> True
bank.deposit(4, "alice", 100)        # -> 100
bank.transfer(5, "alice", "bob", 30) # -> 70
bank.transfer(6, "bob", "alice", 31) # -> None (bob holds 30)
bank.deposit(7, "ghost", 5)          # -> None
```

### Clarifications

- **Does `deposit` create a missing account?** No. It returns `None`.
- **Can an account transfer its whole balance?** Yes; the balance becomes `0`.
- **Do I validate that timestamps increase?** No. They always do.
- **Should I worry about two `Bank` objects?** Each instance is independent.
- **Is there anything beyond these three methods now?** Not yet. Later levels
  add methods to the same class, so keep your state in one obvious place.

Run the provided tests with **Submit**; later levels come with their own test files.

---
Interviewer notes

Graders watch for a clean state model (one dict of balances, not parallel structures that can drift apart) and for failed operations that leave nothing half-applied, such as debiting before checking the target. Candidates stall by over-designing (Account classes, exceptions) in the first ten minutes; this level should take about that long.
