# Product Feed: Part 3

Several listings can resolve to the same product (different sellers, or
fallbacks converging on one item). Merge them into one catalog entry per
SKU.

### What you are given

The output of Part 2: a list of product dicts and `None`s. Every product
dict has `sku: str`, `name: str`, `price: int` (cents), `stock: int`,
`tags: list[str]`.

### What to implement

`merge_listings(products: list[dict | None]) -> list[dict]`

### Rules

1. Skip every `None`.
2. Group products by `sku`. Output **one new dict** per sku, with exactly
   these keys:
   - `sku`
   - `name`: the name of the **first** product with that sku, in input order
   - `price`: the **minimum** price in the group
   - `stock`: the **sum** of the group's stock
   - `tags`: the **union** of the group's tags, **sorted**, with no
     duplicates, as a list
3. Output order is the order in which each sku **first appears** in the
   input.
4. Do not mutate the input products. In particular, the output `tags` list
   must be a new list, never one of the input lists.

### Worked example

```python
merge_listings([
  {"sku": "S1", "name": "Tent", "price": 1999, "stock": 2, "tags": ["camp", "sale"]},
  None,
  {"sku": "S2", "name": "Lamp", "price": 500,  "stock": 1, "tags": []},
  {"sku": "S1", "name": "Tent (XL)", "price": 1499, "stock": 3, "tags": ["xl", "camp"]},
])
# -> [{"sku": "S1", "name": "Tent", "price": 1499, "stock": 5, "tags": ["camp", "sale", "xl"]},
#     {"sku": "S2", "name": "Lamp", "price": 500,  "stock": 1, "tags": []}]
```

### Clarifications

- **A sku appears only once. Does it still get a new dict?** Yes. Tests
  check that the result is not the same object as the input, and that its
  tags are sorted.
- **Sorted how?** Plain string sort, `sorted(...)`.
- **Can `stock` be 0, or prices tie?** Yes; sum and min handle both.
- **Only `None`s, or empty input?** Return `[]`.
- **Scale?** Thousands of products. One pass with a dict keyed by sku is
  enough; avoid re-scanning the list per sku.

Run the provided tests with **Submit**.

---
Interviewer notes

From the Staff Agent Engineer report: "building a paginated list +
processing it to merge items", with the advice to clarify "how duplicates
should be merged" before coding. Here the rules are given; the trap is
mutating the first occurrence in place (tags list shared with the input).
