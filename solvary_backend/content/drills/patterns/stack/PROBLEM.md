# A Stack with dunder methods

Implement a `Stack` that plays well with built-ins: `len(stack)` is its size, an empty stack is falsy, iterating yields items top first, and popping an empty stack raises `IndexError`.

### Signature

```python
class Stack:
    def push(self, item) -> None
    def pop(self)          # IndexError when empty
    def peek(self)         # IndexError when empty
    def __len__(self) -> int
    def __iter__(self)     # top to bottom
```

### Examples

```python
s = Stack()
not s                 # empty is falsy
s.push(1); s.push(2)
len(s) == 2
list(s) == [2, 1]
s.pop() == 2
s.peek() == 1
```

### Idiom

Back the stack with a list; implement `__len__` and `__iter__` so truthiness and `list()` work with no extra methods. Let `list.pop()` raise the `IndexError`.
