# Product Feed: Part 1

A retailer's product API is paginated and flaky. Pull every listing.

### What you are given

- `api` is an object with one method, `api.list_products(cursor=None)`. It
  returns a dict `{"items": [listing, ...], "next_cursor": str | None}`.
- Start with `cursor=None`. `next_cursor` names the next page; `None` means
  this was the last page. A page may have no items and still carry a
  `next_cursor`.
- Each listing is a dict. This part does not look inside it.
- `TransientError` (in the stub) is what `list_products` raises when it
  fails in a retryable way. It fails intermittently but eventually succeeds.

### What to implement

`fetch_products(api, *, max_attempts=5) -> list[dict]`

### Rules

1. **Collect every page, in order,** into one list. Keep the listing dicts
   as they are: same objects, same order, no deduplication.
2. **Retry on `TransientError`,** immediately, with the same cursor.
   `max_attempts` is the **total** number of calls allowed for one page,
   first try included. `max_attempts=1` means no retry. If the last allowed
   call fails, let that `TransientError` propagate.
3. **Only `TransientError` is retried.** Any other exception propagates
   immediately, after a single call.
4. A retry must never duplicate a page's items. Add them only after a
   successful call.

### Worked example

```python
# pages: None -> {items:[a, b], next:"p2"}, "p2" -> {items:[c], next:None}
# list_products fails once on "p2"
fetch_products(api)   # -> [a, b, c]  after 3 calls: None, "p2", "p2"
```

### Clarifications

- **Attempts or retries?** Attempts: total calls per page. This is the
  opposite convention from Conversation History, so read it twice. With
  `max_attempts=5`, a page may fail four times and succeed on the fifth.
- **Does the attempt budget reset per page?** Yes.
- **Should I sleep between retries?** No.
- **Does the API ever loop or return a page twice?** Not in this problem.
  Just follow `next_cursor`.
- **Should I copy the listings?** No. Tests check that the returned dicts
  are the very objects the API returned.
- **Can the feed be empty?** Yes: the first page has no items and
  `next_cursor` is `None`. Return `[]`.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

The Gaijineer and Senior-AI-Engineer (L5) phone-screen variant: "an
endpoint that fails occasionally but eventually succeeds", then
"pagination to retrieve all results", then processing the JSON. Part 1
is deliberately easy; the time pressure is in Parts 2 and 3.
