# Banking System: Part 3

The same `Bank` class grows. Level 3 adds payments that execute later, which
means the bank now has things that happen between operations. The Level 1 and
2 tests still run. This is the level where most candidates lose the clock, so
read the processing rule twice before writing code.

### What to implement

- `schedule_payment(timestamp, account_id, amount, delay) -> str | None`:
  schedule a payment from `account_id` that executes at `timestamp + delay`.
  Return its id, `"payment1"`, `"payment2"`, ... counted globally across all
  accounts, or `None` if the account does not exist (no id is consumed).
- `cancel_payment(timestamp, account_id, payment_id) -> bool`: cancel a
  payment. `True` only if the payment exists, belongs to `account_id`, and is
  still `"PENDING"`; otherwise `False`.
- `get_payment_status(timestamp, account_id, payment_id) -> str | None`: one
  of `"PENDING"`, `"PAID"`, `"FAILED"`, `"CANCELED"`; `None` if the payment
  does not exist or does not belong to `account_id`.

### Rules

- **Processing rule (the trap).** Before handling **any** operation at time
  `T` (every method, from every level), first process every pending payment
  whose execute time is `<= T`, in the order the payments were scheduled. A
  payment due at exactly `T` runs before the operation at `T`.
- Processing a payment: if the balance covers the amount **at that moment**,
  deduct it and mark the payment `"PAID"`; otherwise mark it `"FAILED"`. A
  failed payment is never retried.
- Paid payments count toward the account's total outgoing in `top_spenders`.
  Pending, failed and canceled payments do not.
- `delay` is a positive integer, so a payment is never due the moment it is
  scheduled.

### Worked example

```python
bank = Bank()
bank.create_account(1, "alice")
bank.create_account(2, "bob")
bank.deposit(3, "alice", 100)
bank.schedule_payment(5, "alice", 80, 10)       # -> "payment1" (due at 15)
bank.get_payment_status(14, "alice", "payment1")  # -> "PENDING"
bank.transfer(15, "alice", "bob", 50)           # -> None (payment ran first: 20 left)
bank.get_payment_status(16, "alice", "payment1")  # -> "PAID"
bank.top_spenders(17, 1)                         # -> ["alice(80)"]
```

### Clarifications

- **A payment is due exactly at the timestamp of my next operation. Before or
  after?** Before. The operation sees the post-payment state.
- **Two payments due by the same operation?** They run in scheduling order.
  If the first drains the account, the second fails.
- **Can I cancel at the payment's due timestamp?** No. The payment is
  processed first, so it is `"PAID"` or `"FAILED"` and cancel returns
  `False`.
- **Does cancel need the right account?** Yes. Another account's cancel
  returns `False` and the payment stays `"PENDING"`.
- **Does a failed payment come back if I deposit later?** No, `"FAILED"` is
  permanent.
- **Do queries like `get_payment_status` also trigger processing?** Yes. Every
  method does.

Run the provided tests with **Submit**; earlier levels still run too.

---
Interviewer notes

The reported trap is timestamp order: storing a payment at schedule time is not enough, every later operation has to settle what came due first, including operations that only read. Strong solutions put one `_process_due(now)` call at the top of each method, backed by a heap or an ordered pending list. Candidates stall on the `<=` boundary, on cancel versus due at the same timestamp, and on forgetting that read-only calls also settle payments.
