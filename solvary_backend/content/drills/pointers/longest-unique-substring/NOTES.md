### Why this is idiomatic

- The window is `s[left:right + 1]` and the invariant is "no repeats inside it". Every time you extend `right`, you restore the invariant by moving `left` only as far as needed.
- `max(left, last[c] + 1)` is the subtle line. Without the `max`, a repeat that sits *before* the current window (`"abba"`: the second `b` moves `left` to 2, then the second `a` would move it back to 1) drags `left` backwards and breaks the invariant.
- One `for` loop, no inner `while`: storing the last index lets `left` jump instead of creeping, which is why the dict beats a set here.
- The quadratic version (every start, grow until a repeat) does not finish the last test.

### The habit

"Longest/shortest contiguous run satisfying P" is a sliding window. Name the invariant, decide what extends the window (always `right`) and what restores the invariant (`left`), and keep `best` updated at the end of each step.
