# Conversation History: Part 3

Compaction has to run after **every** message, and tool calls must stay
paired with their results. Turn Part 2 into a class that maintains a
compacted history incrementally.

### What to implement

`class History`:

- `History(limit: int)`
- `append(message: Message) -> None`: add one message, then compact.
- `messages() -> list[Message]`: the current history, in append order,
  after compaction.
- `total_tokens() -> int`: the token total of exactly what `messages()`
  returns.

### Rules

1. **Same policy as Part 2.** System messages are pinned. The most recent
   non-system message is never dropped. Drop from the oldest end until the
   total is `<= limit`, or nothing droppable is left.
2. **Tool units.** An `assistant` message whose `call_id` is not `None`,
   together with the `tool` messages that follow it carrying the same
   `call_id`, form one **unit**. Input guarantee: a `tool` message always
   comes directly after its call, possibly after other `tool` results of the
   same call. An `assistant` message with `call_id=None` is a plain single
   message.
3. **A unit is dropped whole or kept whole.** When the oldest droppable
   message is the start of a unit, drop every message of that unit at once.
   If the unit contains the most recent message, keep the whole unit, even
   if it does not fit on its own.
4. **Performance.** `append` must be **O(1) amortized**. Recomputing the
   whole history on every append will time out (one test does 200,000
   appends). `messages()` may be O(n).

### Worked example

```python
h = History(limit=30)
h.append(sys(5)); h.append(user(10))
h.append(asst(5, call_id="c1")); h.append(tool(5, call_id="c1"))
h.append(user(10))                       # total 35 > 30
h.messages()   # -> [sys, asst(c1), tool(c1), user(10)]   total 25
h.append(user(10))                       # 35 > 30: oldest droppable is asst(c1)
h.messages()   # -> [sys, user(10), user(10)]              total 25
```

At the second overflow the oldest droppable message is `asst(c1)`, which
starts a unit of two messages (10 tokens), so both go together.

### Clarifications

- **Does `messages()` keep system messages at their original positions?**
  Yes. Output is strict append order, with pinned system messages
  interleaved where they were appended, not moved to the front.
- **The newest message is a `tool` result inside a unit that is over the
  limit.** Keep the unit whole. `[user(2), asst(6, "z"), tool(6, "z")]` with
  limit 10 gives `[asst, tool]`, total 12.
- **Can a unit have several tool results?** Yes. `asst(k), tool(k), tool(k)`
  is one unit of three messages.
- **Can a `tool` message survive without its call?** No. Units only ever
  leave together.
- **Why not call Part 2's `compact()` inside `append`?** That is O(n) per
  append and the 200,000-append test will time out. Keep a running total and
  pop from the old end.
- **Must `total_tokens()` match `messages()` exactly?** Yes, after every
  append.

Run the provided tests with **Submit**.

---
Interviewer notes

Two 2026 reports left this third part unfinished at 30 minutes; a running
total plus a deque with O(1) popleft is the expected shape. Pinned system
messages are the trap: a plain deque can't skip them, so keep them in a
separate list and merge by sequence number in `messages()`.
