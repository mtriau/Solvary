# Product Feed: Part 2

Listings point at products, and products can be unavailable. Each product
record carries **fallback IDs** to try instead. Resolve every listing to a
product that is actually available.

### What you are given

- A listing is a dict with a `"product_id"` key (other keys may exist and
  are irrelevant).
- `catalog` maps product id to a product record:
  `{"id": str, "name": str, "available": bool, "fallback_ids": list[str]}`.
- A `product_id` or a fallback id may be missing from the catalog.
- Fallback chains can loop (`a -> b -> a`).

### What to implement

`resolve(listings: list[dict], catalog: dict[str, dict]) -> list[dict | None]`

### Rules

1. One result per listing, in the same order as the listings.
2. For each listing, search for the **first available product** in this
   order: the listing's own `product_id` first; then its fallbacks,
   **depth first**, in list order. "Depth first" means that after trying
   fallback `b`, you explore all of `b`'s own fallbacks (and theirs) before
   moving on to the next sibling fallback `c`.
3. A product that is `available` ends the search for that listing. The
   result is the **catalog's own dict object** for it, not a copy.
4. An id that is not in the catalog is skipped; the search continues.
5. Never visit the same id twice while resolving one listing. That is what
   makes loops terminate. The visited set is per listing; the next listing
   starts fresh.
6. If no available product is reachable, the result for that listing is
   `None`.

### Worked example

```python
catalog = {
  "a": {"id": "a", "available": False, "fallback_ids": ["b", "c"]},
  "b": {"id": "b", "available": False, "fallback_ids": ["d"]},
  "c": {"id": "c", "available": True,  "fallback_ids": []},
  "d": {"id": "d", "available": True,  "fallback_ids": ["a"]},
}
resolve([{"product_id": "a"}, {"product_id": "zzz"}], catalog)
# -> [catalog["d"], None]
```

First listing: `a` is unavailable, so try its first fallback `b`; `b` is
unavailable, so try `b`'s fallback `d`; `d` is available, done. `c` is never
reached even though it is available, because depth-first finishes `b`'s
branch first. Second listing: `"zzz"` is not in the catalog, so nothing is
reachable.

### Clarifications

- **The listing's product is itself available. Do I still look at
  fallbacks?** No. Return it directly.
- **Does depth-first versus breadth-first matter?** Yes. In the example,
  breadth-first would give `c`. The tests expect `d`.
- **How deep can a chain go?** About 500 links in a straight line. Recursion
  stays under Python's default limit at that depth, but an explicit stack is
  safer.
- **An available product sits behind a loop?** It is found if it is reached
  before the loop closes. `a -> [b]`, `b -> [a, c]` with `c` available gives
  `c`: `a` is skipped as already visited, then `c` is tried.
- **A product lists itself as a fallback?** Skipped as already visited; if
  it is unavailable, the result is `None`.
- **Empty `listings`?** Return `[]`.

Run the provided tests with **Submit**.

---
Interviewer notes

The reported wording: "the response contains a product list where
products carry fallback IDs; iterate the list and resolve each product's
eventual set of IDs into product objects." Depth-first order and the
cycle guard are the follow-up questions. Expect a recursive first draft;
ask about the cycle before revealing the test.
