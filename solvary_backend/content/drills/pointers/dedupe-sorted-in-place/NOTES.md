### Why this is idiomatic

- Two pointers over one list: `read` visits everything, `write` marks the end of the finished prefix. The invariant is in the comment: `nums[:write]` is the deduplicated answer so far. Say it before you write the loop.
- Comparing with `nums[write - 1]` (the last kept value) rather than `nums[read - 1]` is the one subtle point; both happen to work on sorted input, but comparing with what you kept is what generalises.
- `del nums[write:]` at the end would also shrink the list, but the contract here is LeetCode's: return the count, leave the tail alone.
- `list(dict.fromkeys(nums))` solves the value problem but allocates; this drill is about the in-place shape, which shows up as "move zeroes", "remove element", "compact".

### The habit

In-place compaction is always "a read pointer that is the loop, a write pointer you advance only when you keep something". Return or truncate at `write`.
