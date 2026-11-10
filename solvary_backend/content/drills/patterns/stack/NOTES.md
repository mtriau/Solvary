### Why this is idiomatic

- Python asks objects how to behave through dunder methods. Implementing `__len__` makes `len(s)` work *and* makes an empty stack falsy, because truthiness falls back to `__len__` when there is no `__bool__`. One method, two behaviours; no `is_empty()` needed.
- `__iter__` returning `reversed(self._items)` gives top-first iteration lazily, so `list(s)`, `for item in s` and `in` all work.
- `list.pop()` and `self._items[-1]` already raise `IndexError` on an empty list. Re-raising your own exception would only add code; let the built-in behaviour through.
- The leading underscore on `_items` marks it as internal without the ceremony of properties.
- `__repr__` is optional but cheap, and it makes debugging output readable.

### The habit

When your class has a size, implement `__len__`. When it is a container, implement `__iter__`. Then use the built-ins instead of inventing `size()`, `is_empty()` and `to_list()`.
