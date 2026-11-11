### Why this is idiomatic

- `dict.fromkeys(items)` builds a dict with one key per distinct item, in first-seen order, in C. `list(...)` reads the keys back. One line, O(n).
- `list(set(items))` loses the order and is the most common wrong answer.
- The explicit version is the pattern underneath, and it is fine too:

  ```python
  seen = set()
  out = []
  for x in items:
      if x not in seen:
          seen.add(x)
          out.append(x)
  ```

  What you must never write is `if x not in out`: that is a list scan per item, quadratic, and the last test is there to make it hurt.

### The habit

"Unique, in order" is `dict.fromkeys`. "Unique, order irrelevant" is `set`. "Have I seen this before" is a `set` you add to as you go.
