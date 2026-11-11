### Why this is idiomatic

- A bounded deque is a sliding window that maintains itself. No `if len(window) > k: window.pop(0)`, which on a list is O(k) per step anyway.
- `len(window)` is the current window size, so the warm-up phase ("fewer than k so far") needs no special case.
- If `k` were huge you would keep a running total instead of `sum(window)`: add the new value, subtract the one that fell off. The deque still manages the membership; say this as the follow-up.

### The habit

"Last k things" is `deque(maxlen=k)`. Any time you catch yourself writing `list.pop(0)`, it should have been a deque.
