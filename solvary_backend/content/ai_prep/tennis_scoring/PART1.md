# Tennis Scoring: Part 1

Reddit asks this as a 60-minute design-and-extend screen for SWE and MLE
roles: a `Game`, then a `Set` built on it, then a `Match`, then a harness.
Candidates typically burn 15 to 20 minutes clarifying the rules, and
interviewers want the `Game` built completely before you touch `Set`, real
error handling, and some tests of your own in the last minutes. A first-hand
candidate ran out of time on the third part, so keep this one tight.

### What to implement

Module `tennis_scoring`, class `Game`, a single game between players `"A"`
and `"B"`:

- `Game()`: a new game at love-all.
- `record_point(player: str) -> None`: the named player wins the next
  point. Raises `ValueError` if `player` is not exactly `"A"` or `"B"`, or
  if the game is already decided.
- `score() -> str`: the conventional call, `A`'s count first (see Rules).
- `winner() -> str | None`: `"A"`, `"B"`, or `None` while undecided.
- `points() -> tuple[int, int]`: raw point counts `(A, B)`.

### Rules

1. Points are called `0`, `15`, `30`, `40` for a player's none, first,
   second and third point. A fourth point wins the game, unless the
   opponent also has at least three points (see rules 2 to 4).
2. A game is won by the first player to reach **4 points with a lead of at
   least 2**. So 4-0, 4-1 and 4-2 are wins; 4-3 is not.
3. While both players have at least 3 points, the call is never `40-40`.
   Level scores read `"deuce"`. If one player leads by one the call is
   `"advantage A"` or `"advantage B"`.
4. If the player with advantage wins the next point, they win the game. If
   the other player wins it, the score goes back to `"deuce"`.
5. There is **no limit** to the number of deuces.
6. Before deuce the call is `"<A call>-<B call>"`, for example `"30-15"` or
   `"40-30"`. Once decided, the call is `"game A"` or `"game B"`.
7. An invalid call to `record_point` must leave the game unchanged.

### Worked example

```python
g = Game()
g.score()            # -> "0-0"
g.record_point("A")
g.record_point("B")
g.record_point("A")
g.score()            # -> "30-15"
g.record_point("A")
g.score()            # -> "40-15"
g.points()           # -> (3, 1)
g.record_point("B")
g.record_point("B")
g.score()            # -> "deuce"
g.record_point("B")
g.score()            # -> "advantage B"
g.record_point("A")
g.score()            # -> "deuce"
g.record_point("A")
g.record_point("A")
g.winner()           # -> "A"
g.score()            # -> "game A"
g.record_point("B")  # raises ValueError
```

### Clarifications

- **What does `score()` say the first time both players reach three
  points?** `"deuce"`, never `"40-40"`.
- **Can a game end 4-2?** Yes. It cannot end 2-0 or 3-0, and 4-3 is
  not over.
- **What if advantage is lost?** Back to `"deuce"`, and it can repeat any
  number of times. Twenty deuces in a row must work.
- **Which player is named first in `"30-15"`?** `A`.
- **What about a point recorded after the game ended?** `ValueError`, and
  `points()` and `score()` stay as they were.
- **Lowercase `"a"`, an empty string, or `"AB"`?** `ValueError`.
- **Does `winner()` raise while the game is undecided?** No, it returns
  `None`.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

Graders watch whether the win rule is expressed once (first to 4, lead of 2)
rather than as a pile of special cases, which is what avoids the classic
"game ends on 2-0" and "deuce only works a few times" bugs. They also check
that a decided game rejects further points and that bad input does not
corrupt state. Part 2 builds on this by composition, so a clean `points()`
and a small public surface pay off. Later follow-ups at Reddit: sides switch
after odd-numbered games, serving rotation, and "what is the score after the
17th point?".
