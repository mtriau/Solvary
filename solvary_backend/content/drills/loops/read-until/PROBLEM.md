# Read until a sentinel

`read` is a function that returns the next line each time it is called. Collect lines until it returns `sentinel` (not included), and do not call `read` again after that.

### Signature

`def read_until(read: Callable[[], str], sentinel: str) -> list[str]`

### Examples

```python
lines = iter(["a", "b", "", "c"])
read_until(lambda: next(lines), "") == ["a", "b"]
```

### Idiom

The two-argument form of `iter`: `iter(read, sentinel)` is an iterator that calls `read()` until it returns `sentinel`. `list(iter(read, sentinel))` is the whole function. If you write the loop by hand, use the walrus: `while (line := read()) != sentinel:`.
