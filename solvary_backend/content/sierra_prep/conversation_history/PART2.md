# Conversation History: Part 2

The model has a context window. Before each model call, the history must fit
a token budget. Write the function that trims it.

### What to implement

`compact(messages: list[Message], limit: int) -> list[Message]`

`messages` is in chronological order (oldest first). Each message has a
`tokens` count. The total of a list is the sum of its messages' `tokens`.

### Rules

1. **Already fits:** if the total is `<= limit`, return a **new list** with
   the same messages in the same order.
2. **Otherwise, drop from the oldest end,** one message at a time, until the
   total is `<= limit`.
3. **Two kinds of message are never dropped,** and still count toward the
   total:
   - every message with `role == "system"`, wherever it sits in the list;
   - the **most recent** message (the last one in the list).

   When the oldest remaining message is one of these, skip over it and drop
   the next-oldest droppable message instead.
4. **Give up gracefully:** if everything droppable is gone and the total is
   still over `limit`, return what is left.
5. Keep relative order. Never mutate the input list. `compact([], 10) -> []`.

### Worked example

```python
msgs = [sys(5), user(10), asst(10), user(10)]   # tokens in parentheses, total 35
compact(msgs, 100)   # -> all four                       (35 <= 100)
compact(msgs, 35)    # -> all four                       (exactly at the limit)
compact(msgs, 25)    # -> [sys, asst, user]   total 25   (dropped the first user)
compact(msgs, 20)    # -> [sys, last user]    total 15   (dropped user, then asst)
compact(msgs, 3)     # -> [sys, last user]    total 15   (nothing else can go)
```

### Clarifications

- **Can a system message be in the middle, or can there be several?** Yes.
  They are pinned wherever they appear: `[user, system, user, system, user]`
  keeps both system messages.
- **The last message alone is bigger than the limit. What then?** Keep it.
  `compact([u(1), u(1), u(500)], 10) -> [u(500)]`.
- **A message has `tokens == 0`. Is it still dropped?** Yes, when it is the
  oldest droppable one, even though dropping it does not change the total.
- **If the input already fits, can I return the same list object?** No.
  Return a fresh list; callers may append to the result.
- **Is the input ever mutated?** Never. Tests check the original list
  afterwards.
- **Do roles other than `"system"` get special treatment?** No. `user`,
  `assistant` and `tool` are all droppable.

Run the provided tests with **Submit**.

---
Interviewer notes

"Drop the oldest messages until it fits" is the reported wording; the
pinned-system and keep-latest rules are the follow-ups interviewers add.
Watch for solutions that drop a system message, or that return the input
list object and later mutate it.
