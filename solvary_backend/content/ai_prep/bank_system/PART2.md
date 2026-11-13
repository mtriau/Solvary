# Banking System: Part 2

The same `Bank` class grows. Level 2 adds a ranking of accounts by how much
money they have sent out. The Level 1 tests still run, so do not break them.

### What to implement

`top_spenders(timestamp, n) -> list[str]`

- Return up to `n` entries of the form `"account_id(total_outgoing)"`.
- An account's **total outgoing** is the sum of the amounts of its
  **successful** outgoing transfers. (Level 3 will add payments to this.)
- Sort by total outgoing **descending**; break ties by account id
  **ascending**.
- If fewer than `n` accounts exist, return all of them.

### Rules

- Every existing account is eligible, including those that never spent
  anything (they show as `"id(0)"`).
- Deposits, incoming transfers and failed operations do not count.

### Worked example

```python
bank = Bank()
for t, name in enumerate(["amy", "bob", "cat"], start=1):
    bank.create_account(t, name)
bank.deposit(4, "amy", 100)
bank.deposit(5, "bob", 100)
bank.transfer(6, "amy", "cat", 30)
bank.transfer(7, "bob", "cat", 30)
bank.transfer(8, "cat", "amy", 10)
bank.top_spenders(9, 2)   # -> ["amy(30)", "bob(30)"]
bank.top_spenders(10, 9)  # -> ["amy(30)", "bob(30)", "cat(10)"]
```

### Clarifications

- **What if `n` is `0`, or there are no accounts?** Return an empty list.
- **Are zero-spend accounts included?** Yes, after everyone who spent more.
- **Ties?** Same total: alphabetical by account id (plain string order).
- **Does the format have spaces?** No: `"amy(30)"`, and the list is a plain
  Python list of strings.
- **Efficiency?** Sorting all accounts per call is fine here.

Run the provided tests with **Submit**; earlier levels still run too.

---
Interviewer notes

Graders look for a running per-account outgoing total updated at transfer time (not recomputed from a log) and a single sort key such as `(-total, id)`. Candidates stall on forgetting zero-spend accounts or on counting a transfer before the funds check. Level 3 will add a second way to spend, so a helper that records outgoing money pays off.
