### Why this is idiomatic

- The slice `start:stop:step` expresses "every second element from here" directly. `[::2]` and `[1::2]` are instantly recognisable to Python readers; the `enumerate` + `i % 2` version is three times longer.
- Slices always return new lists, so the inputs are never shared (the suite checks).
- Slicing is forgiving: on an empty or one-element list the slices are simply empty, no bounds checks needed.

### The habit

Learn the three-part slice. `[::-1]` (reversed), `[::2]` (every other), `[-3:]` (last three) cover most positional selections.
