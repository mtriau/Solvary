# Merchandise Catalog: Part 2

The service returns a catalog. Answer questions about items and how they
relate to each other.

### What you are given

`catalog` is a dict from item id to an item record. Every record has all
three keys:

```python
{"name": str, "attributes": {str: value}, "related": [item ids]}
```

An id in a `related` list may be missing from the catalog (`"ghost"`
below). In this part the relationships contain **no cycles**.

### What to implement

- `get_attribute(catalog, item_id, key, default=None)`: the value of
  attribute `key` on the item, or `default` if the item does not exist or
  has no such attribute.
- `related_items(catalog, item_id) -> list[str]`: the item's **direct**
  related ids, in the order they appear in the item's own `related` list,
  skipping ids that are not in the catalog. `[]` for an unknown item.
- `related_tree(catalog, item_id) -> dict | None`: the full relationship
  tree below the item, built from `related_items` at every level:
  `{"id": item_id, "related": [subtree, ...]}`. `None` for an unknown item.

### Worked example

```python
cat = {
  "tent":  {"name": "Tent",  "attributes": {"season": 3}, "related": ["stakes", "lamp", "ghost"]},
  "stakes":{"name": "Stakes","attributes": {},            "related": []},
  "lamp":  {"name": "Lamp",  "attributes": {"lumens": 300}, "related": ["battery"]},
  "battery":{"name":"AA",    "attributes": {},            "related": []},
}
get_attribute(cat, "lamp", "lumens")        # -> 300
get_attribute(cat, "lamp", "weight", 0)     # -> 0
related_items(cat, "tent")                  # -> ["stakes", "lamp"]
related_tree(cat, "tent")
# -> {"id": "tent", "related": [
#       {"id": "stakes", "related": []},
#       {"id": "lamp", "related": [{"id": "battery", "related": []}]}]}
```

### Clarifications

- **Order of related items: the item's list, or the catalog's key order?**
  The item's own `related` list order. Catalog key order is irrelevant.
- **An item has no related items?** `related_tree` is
  `{"id": ..., "related": []}`.
- **The same item is reachable through two different branches?** It appears
  in both branches, each with its own subtree. The result is a tree, not a
  deduplicated graph.
- **Does the tree contain names or attributes?** No. Only `"id"` and
  `"related"`.
- **Must the catalog stay untouched?** Yes. Build new dicts; never store
  subtrees in the catalog records.
- **How deep?** Chains of about 300 items. Recursion survives that in
  Python, but an explicit stack is also fine and becomes useful in Part 3.

Run the provided tests with **Submit**.

---
Interviewer notes

Reported wording: "given this merchandise catalog, if I give you item A,
can you find all the items related to it, then the related items'
children". The candidate who did nested while/for loops was told DFS or
BFS would have scored better; the follow-up is "how would you improve
the solution, and why did you choose it over alternatives?"
