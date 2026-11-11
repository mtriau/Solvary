### Why this is idiomatic

- "Group by X" is `defaultdict(list)` keyed by X, every time. Here X is a canonical form that is equal for all anagrams: the sorted letters.
- `"".join(sorted(word))` is the usual key. `tuple(sorted(word))` works too (keys only need to be hashable). A 26-count tuple is the O(len) version interviewers sometimes ask for as a follow-up.
- Because dicts keep insertion order, `list(groups.values())` already matches "order of first appearance" with no sorting step.

### The habit

Before grouping anything, ask "what is the key that makes equal things collide?" and build the dict around it.
