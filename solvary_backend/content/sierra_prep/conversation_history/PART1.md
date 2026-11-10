# Conversation History: Part 1

You are building the message-history layer of a customer-service agent. The
conversation store is paginated and flaky: you get one page per call, and a
call can fail. Pull the whole conversation.

### What you are given

The stub defines:

- `Message`: a frozen dataclass with `id`, `role`, `text`, `tokens` (and
  `call_id`, unused until Part 3). Messages compare by value.
- `TransientError`: raised by the page fetcher when a call fails in a
  retryable way.
- `PaginationError`: for you to raise when the API misbehaves.

`fetch_page` is a **function** (not an API object). You call it as
`fetch_page(cursor)` and it returns a pair `(messages, next_cursor)`:

- `messages` is a `list[Message]` for that page. It can be empty.
- `next_cursor` is a string naming the next page, or `None` when this was
  the last page.
- The first page is fetched with `cursor=None`.

### What to implement

`fetch_all(fetch_page, *, max_retries=3) -> list[Message]`

### Rules

1. **Walk the pages in order.** Start at `None`, follow `next_cursor` until
   it is `None`. Concatenate the pages' messages, in order, into one list.
   An empty page that still carries a `next_cursor` is normal: keep going.
2. **Retry the same cursor on `TransientError`.** After a failure, call
   `fetch_page` again with the same cursor. `max_retries` is the number of
   *extra* attempts per cursor, so each cursor gets at most
   `max_retries + 1` calls. `max_retries=0` means one attempt, no retries.
   If the last allowed attempt fails, let that `TransientError` propagate.
3. **Never lose or duplicate a page.** Add a page's messages to the result
   only once, after the call that returned it succeeded.
4. **Detect a looping API.** If `next_cursor` is a cursor you have already
   fetched (including `None`, the first one), raise `PaginationError`
   instead of fetching it again.
5. **No wasted calls.** When nothing fails, call `fetch_page` exactly once
   per page.

### Worked example

```python
pages = {
    None: ([m1, m2], "c1"),
    "c1": ([],       "c2"),
    "c2": ([m3],     None),
}
fetch_all(lambda c: pages[c])   # -> [m1, m2, m3]   (3 calls)
```

Call `None` gives `[m1, m2]` and next `"c1"`. Call `"c1"` gives an empty
page and next `"c2"`. Call `"c2"` gives `[m3]` and next `None`, so stop.

With `max_retries=2` and a fetcher that fails twice on `"c1"` and then
succeeds, the calls are `None, "c1", "c1", "c1"` and the result is the same.
If it failed three times on `"c1"`, the third failure is raised.

### Clarifications

- **Is `max_retries` counting calls or retries?** Retries. `max_retries=3`
  allows 4 calls for one cursor.
- **Does the retry budget reset for each cursor?** Yes. It is per cursor,
  not per whole fetch.
- **What counts as "already used" for the loop check?** Every cursor you
  have called `fetch_page` with, `None` included. One test points a later
  page's `next_cursor` back at an earlier page.
- **Should I wait between retries?** No. Retry immediately.
- **Do I need to handle exceptions other than `TransientError`?** Not in
  this part. Let them propagate.
- **Is an empty conversation possible?** Yes: the first page is empty with
  `next_cursor=None`. Return `[]`.
- **How many pages can there be?** Hundreds. A simple loop is fine; avoid
  anything quadratic in the number of pages.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

Reconstructed from the most-reported Sierra phone screen (nine first-hand
reports, Nov 2025 to Oct 2026): "fetch pages until no more data", retries on
a flaky endpoint, then transform, then compaction. Candidates lose time to
plumbing, not algorithms; watch for off-by-one retry counts and for the
retry loop re-appending a page.
