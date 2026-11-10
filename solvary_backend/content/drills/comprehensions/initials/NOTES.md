### Why this is idiomatic

- A set comprehension `{... for ... if ...}` builds the set in one expression, and the set type itself removes duplicates. No `if initial not in seen` bookkeeping.
- The filter `if name.strip()` uses truthiness: an empty string is falsy, so blank names drop out without comparing to `""`.
- `strip()` is called twice; that is fine. Clarity beats saving one call on a short string. (If it bothered you, a walrus `if (clean := name.strip())` would let you reuse it.)

### The habit

When uniqueness is part of the requirement, build a set directly rather than a list that you de-duplicate afterwards.
