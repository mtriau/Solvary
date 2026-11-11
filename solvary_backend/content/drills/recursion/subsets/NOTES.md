### Why this is idiomatic

- `chosen.append(x)`, recurse, `chosen.pop()`: choose, explore, un-choose. Every backtracking problem (subsets, permutations, combinations, N-queens) is this triple around a recursive call, with the problem's rules deciding what is allowed at each step.
- `start` is what prevents duplicates: each level only considers items after the last one chosen, so `[1, 2]` and `[2, 1]` cannot both appear.
- Recording `chosen.copy()` (or `chosen[:]`) matters because `chosen` is mutated afterwards; appending `chosen` itself makes every entry the same empty list at the end. The last test catches it.
- Alternatives worth knowing: `itertools.combinations(items, r)` for each r, or the bit-mask loop `for mask in range(1 << n)`. Both are idiomatic; the backtracking form is the one that generalises when constraints are added.

### The habit

Say "choose, explore, un-choose" as you type the three lines. Decide what the recursion's parameters mean (`start` = "nothing before this index may be chosen") before writing the loop.
