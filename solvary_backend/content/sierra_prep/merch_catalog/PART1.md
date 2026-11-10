# Merchandise Catalog: Part 1

A call to the merchandise service throws intermittently. Wrap it in a retry
helper with exponential backoff and an overall timeout.

### What to implement

```python
retry(fn, *, attempts=5, base_delay=0.1, factor=2.0, max_delay=2.0,
      timeout=None, retry_on=(Exception,), sleep=time.sleep, clock=time.monotonic)
```

`fn` is a zero-argument callable. The stub gives you the signature.

### Rules

1. Call `fn()`. If it returns, return that value immediately (whatever it
   is, including `None`).
2. If it raises an exception that is an instance of one of the `retry_on`
   types (subclasses count), sleep and try again. Any other exception
   propagates **immediately**, unchanged, with no further calls.
3. Make at most `attempts` calls in total. If the last allowed call fails,
   re-raise **that** exception. Never sleep after the final failure.
4. **Backoff.** Before retry number `k` (`k = 1, 2, 3, ...`), sleep
   `min(base_delay * factor ** (k - 1), max_delay)` seconds. With the
   defaults: 0.1, 0.2, 0.4, 0.8, 1.6, 2.0, 2.0, ...
5. **Timeout.** `timeout` is a total budget in seconds, measured with
   `clock()` from just before the first call. Before each sleep, compute
   `elapsed + next_sleep`; if that **exceeds** `timeout`, do not sleep:
   re-raise the last exception instead. `timeout=None` means no budget.
6. **Always use the injected `sleep` and `clock`.** The tests pass fakes
   that record sleeps and advance a fake clock. Never call the `time` module
   directly.

### Worked example

```python
calls = []
def flaky():
    calls.append(1)
    if len(calls) < 3:
        raise ConnectionError("503")
    return "ok"

slept = []
retry(flaky, sleep=slept.append)   # -> "ok"
slept                              # -> [0.1, 0.2]
```

Call 1 fails, sleep 0.1; call 2 fails, sleep 0.2; call 3 succeeds.

With `timeout=0.5` and a function that always fails: call 1 fails, sleep
0.1 (elapsed 0.1); call 2 fails, sleep 0.2 (elapsed 0.3); call 3 fails, and
the next sleep would be 0.4, but 0.3 + 0.4 = 0.7 > 0.5, so the third
failure is raised after exactly 3 calls.

### Clarifications

- **`attempts=1`?** One call, no sleep, re-raise on failure.
- **Is the timeout check `>` or `>=`?** Strictly greater. With
  `timeout=0.35`, sleeps of 0.1 and 0.2 (total 0.3) are allowed.
- **When is the clock read?** Once at the start, and again whenever you
  decide whether to sleep. Reading it even when `timeout` is `None` is
  harmless.
- **Does time spent inside `fn()` count toward the timeout?** Yes. Elapsed
  is `clock() - start` at the moment you decide whether to sleep, so it
  includes everything so far.
- **`retry_on` defaults to `(Exception,)`. Does that retry everything?**
  Everything that is an `Exception`. The tests also pass narrower tuples
  such as `(ConnectionError, TimeoutError)`, in which case a `KeyError` must
  propagate at once.
- **Any jitter?** No. Deterministic delays only.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

From the APX (early-career) live Python round: "here's some Python code
that currently throws a basic error, add exponential retries so it keeps
trying", bank wording "an async exponential retry mechanism with timeouts
and backoff". Kept synchronous here with injectable sleep/clock so the
suite runs instantly; the same structure works with `asyncio.sleep`.
