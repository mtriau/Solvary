# Credit Tracker: Part 1

Customers receive credit grants that expire. Implement `CreditTracker`:

- `add_credit(start: int, end: int, amount: int) -> None`
  Record a grant of `amount` credits that is active at every time `t` with
  `start <= t <= end` (inclusive on both ends).
- `check_credit(t: int) -> int`
  Return the total credit active at time `t`.

```python
c = CreditTracker()
c.add_credit(1, 10, 100)
c.add_credit(5, 7, 50)
c.check_credit(0)     # -> 0
c.check_credit(1)     # -> 100
c.check_credit(5)     # -> 150
c.check_credit(7)     # -> 150
c.check_credit(8)     # -> 100
c.check_credit(11)    # -> 0
```

Run the provided tests: `pytest credit_tracker -q`. Later parts come with
their own test files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*
