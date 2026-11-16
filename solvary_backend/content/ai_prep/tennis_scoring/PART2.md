# Tennis Scoring: Part 2

The same module grows a `Set`: a run of games until one player has won
enough of them. The Part 1 tests still run alongside the new ones. Build it
by having the `Set` hold a `Game` rather than copying the scoring rules.

### What to implement

Class `Set` in `tennis_scoring`:

- `Set()`: a new set at 0-0 with a fresh game.
- `record_point(player: str) -> None`: forwards the point to the current
  game. When that game is decided, it is added to the games tally and a new
  game starts automatically. Raises `ValueError` for an unknown player, or
  for any point once the set is won.
- `games() -> tuple[int, int]`: games won `(A, B)`.
- `in_tiebreak() -> bool`: `True` while the tiebreak game is being played.
- `score() -> str`: `"<gamesA>-<gamesB>, <current game score>"` while in
  progress, e.g. `"4-3, 30-15"`; `"set A"` or `"set B"` once won.
- `winner() -> str | None`.

### Rules

1. A set is won by the first player to **6 games with a lead of at least
   2**: 6-0 to 6-4 are wins, **6-5 is not**; at 6-5 the leader needs a
   seventh game (7-5).
2. At **6-6** a tiebreak game is played instead of a normal game.
3. The tiebreak is won by the first player to **7 points with a lead of at
   least 2**, with no upper bound (8-6, 9-7, 15-13...). Winning it wins the
   set 7-6.
4. Tiebreak points are not called 15/30/40. Its score reads as raw
   points, `"<A>-<B>"`, so inside a set `"6-6, 3-2"`.
5. A game that has just finished is not shown: the score of the next fresh
   game is `"0-0"`, so `"1-0, 0-0"` right after the first game.
6. The normal game keeps all the Part 1 rules (deuce, advantage).

### Worked example

```python
s = Set()
for p in "AAAA":
    s.record_point(p)
s.games()            # -> (1, 0)
s.score()            # -> "1-0, 0-0"
s.record_point("B")
s.score()            # -> "1-0, 0-15"
# ... play on until the games are 6-6:
s.in_tiebreak()      # -> True
s.score()            # -> "6-6, 0-0"
s.record_point("A")
s.record_point("A")
s.record_point("B")
s.score()            # -> "6-6, 2-1"
# ... A takes the tiebreak 7-5:
s.games()            # -> (7, 6)
s.score()            # -> "set A"
s.in_tiebreak()      # -> False
s.record_point("B")  # raises ValueError
```

### Clarifications

- **Is 6-5 a finished set?** No. The leader needs 7-5. If the trailing
  player wins the next game it is 6-6 and the tiebreak starts.
- **When exactly does the tiebreak start?** At 6-6 in games, and only then.
- **Does the tiebreak need a lead of two?** Yes: 7-6 in points continues.
  It has no cap.
- **What does `games()` say after a tiebreak?** `(7, 6)` or `(6, 7)`.
- **What does `in_tiebreak()` say once the set is won?** `False`.
- **Does the tiebreak change who is named first in a score?** No, `A`
  first.
- **Can a `Game` still be used on its own?** Yes; its behaviour is
  unchanged.

Run the provided tests with **Submit**.

---
Interviewer notes

The point of this part is composition: `Set` owns a `Game` and only reacts
when it finishes, instead of one giant state machine tracking points and
games together. A tiebreak is the same shape of object with a different win
rule and display, so a flag or subclass on `Game` keeps `Set` simple. Graders
check the terminal-state errors, the 6-5 and 6-6 boundaries, and that the
tiebreak has no hard cap. Part 4 and 5 follow-ups: players switch sides after
every odd-numbered game, and a serving rotation (which flips in a tiebreak
after the first point and then every two points).
