# Event Streams: Part 1

An agent run produces events from several sources at once: the model, each
tool it calls, and the customer channel. Each source hands you its events
already in time order. Build the merged timeline. This part is a warm-up;
the next parts make the sources live and then add delayed delivery, so
think about what you would keep if the sources were not lists.

### What to implement

`merge_streams(streams: list[list[Event]]) -> list[Event]`

- An `Event` is a dict with at least `"ts"` (an `int` timestamp), `"source"`
  (a `str`) and `"text"` (a `str`). Other keys may be present; pass events
  through untouched (the same objects, not copies).
- Each inner list is **sorted by `ts`** (non-decreasing). Lists may be
  empty, and `streams` itself may be empty.
- Return every event from every stream, in a single list sorted by `ts`.
- **Ties:** events with the same `ts` keep the order of their streams
  (everything from `streams[0]` before `streams[1]`), and within one stream
  keep their original order.

### Worked example

```python
model = [{"ts": 1, "source": "model", "text": "thinking"},
         {"ts": 4, "source": "model", "text": "reply"}]
tool = [{"ts": 2, "source": "search", "text": "query"},
        {"ts": 4, "source": "search", "text": "3 results"}]
chat = [{"ts": 3, "source": "customer", "text": "hello?"}]

[e["text"] for e in merge_streams([model, tool, chat])]
# -> ["thinking", "query", "hello?", "reply", "3 results"]
#    ("reply" before "3 results": both ts 4, model is the earlier stream)
```

### Clarifications

- **Can I just concatenate and sort?** For this part, yes. Expect the next
  part to take that away.
- **Do I need to validate that the streams are sorted?** No. Assume they
  are.
- **Should the input lists be modified?** No.
- **Timestamps:** non-negative ints. Duplicates across and within streams
  are normal.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

A February 2026 technical phone screen is described (behind a login) as
"coding questions about stream processing and merging multiple streams",
three questions, with a test harness implied. Only the teaser is public,
so the three parts here are a reconstruction in the usual expand-your-code
style. Part 1 accepts concatenate-and-sort; note whether the candidate
mentions a k-way merge or `heapq.merge` unprompted.
