### Why this is idiomatic

- The key function converts the string into something that compares the way you want (a tuple of ints), and `sorted` does the rest. The strings themselves are returned untouched.
- Tuples compare element by element and a shorter tuple that is a prefix of a longer one sorts first, so `(1, 2) < (1, 2, 1)` falls out of the data model.
- `tuple(int(part) for part in v.split("."))` is the readable form; `tuple(map(int, v.split(".")))` is the same thing and also fine.

### The habit

When the natural order of your data is not the string order, write a key that maps each item to a tuple that *does* have the natural order.
