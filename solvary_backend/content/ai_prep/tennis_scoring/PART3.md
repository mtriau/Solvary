# Tennis Scoring: Part 3

The same module grows a `Match` and a small harness that replays a string of
points. Part 1 and Part 2 tests still run alongside the new ones. This is
the part where Reddit candidates run out of time, so reuse `Set` as is.

### What to implement

Class `Match(best_of: int = 3)` in `tennis_scoring`:

- `Match(best_of=3)`: only `3` and `5` are valid; anything else raises
  `ValueError`.
- `record_point(player: str) -> None`: forwards the point to the current
  set. When that set is decided, its final games are recorded and a new set
  starts, unless the match is over. Raises `ValueError` for an unknown
  player, or for any point once the match is won.
- `sets() -> list[tuple[int, int]]`: final games `(A, B)` of every
  completed set, in order, **plus the current set's games as the last
  element while the match is in progress**.
- `score() -> str`: `"<setsA>-<setsB> sets, <set score>"` while in
  progress, e.g. `"1-0 sets, 4-3, 30-15"`; `"match A"` or `"match B"` once
  won.
- `winner() -> str | None`.

And a module-level function:

- `play(points: str, best_of: int = 3) -> list[str]`: feeds each character
  (`"A"` or `"B"`) into a fresh `Match` and returns `score()` after **every**
  point, so the list has one entry per character. An invalid character, a
  point after the match has ended, or an invalid `best_of` raises
  `ValueError`.

### Rules

1. The match is won by the first player to win `ceil(best_of / 2)` sets: 2
   for best of 3, 3 for best of 5.
2. Each set follows the Part 2 rules, including the 6-6 tiebreak.
3. Right after a set is decided (and the match is not over) a fresh set
   starts, so the score reads like `"1-0 sets, 0-0, 0-0"`.
4. Once the match is over, `sets()` lists only the completed sets.
5. `play("")` returns `[]`.

### Worked example

```python
m = Match()
m.score()                     # -> "0-0 sets, 0-0, 0-0"
# A wins the first set 6-0 (24 points), then:
m.score()                     # -> "1-0 sets, 0-0, 0-0"
m.sets()                      # -> [(6, 0), (0, 0)]
# ... play on to 4-3 in games and 30-15:
m.score()                     # -> "1-0 sets, 4-3, 30-15"

play("AAB")
# -> ["0-0 sets, 0-0, 15-0", "0-0 sets, 0-0, 30-0", "0-0 sets, 0-0, 30-15"]
play("A" * 48)[-1]            # -> "match A"   (three-set match, 48 love points)
play("A" * 49)                # raises ValueError
play("AXB")                   # raises ValueError
```

### Clarifications

- **Does `play` return only the final score?** No, one string per point.
- **What does the entry for the very last point of a set show?** The state
  after it: the new set at `0-0, 0-0` (or `match A` if that ended the
  match).
- **Is `best_of=1` or `best_of=4` allowed?** No, `ValueError`.
- **Is lowercase `"a"` or a space a valid character in `play`?**
  No, `ValueError`.
- **Does `play` share state between calls?** No, each call uses a fresh
  `Match`.
- **Is the number of sets in `sets()` always at most `best_of`?** Yes.

Run the provided tests with **Submit**.

---
Interviewer notes

Graders look for a three-level composition, `Match` owning `Set` owning
`Game`, with one `record_point` that delegates downward and with terminal
states rejecting further points at every level. `play` should be a thin loop
over the public API rather than a second implementation of the scoring. The
real Reddit loop continues with side switches after odd games, serving
rotation, polymorphic best-of-3 and best-of-5 without duplicated logic, and
history queries like "score after the 17th point"; this is why finishing
early and writing your own tests is the strong signal.
