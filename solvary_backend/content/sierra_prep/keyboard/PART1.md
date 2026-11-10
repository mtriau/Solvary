# Keyboard: Part 1

Model the text buffer behind an input box. This part is a warm-up; the next
parts add undo/redo and then a cursor on top of your class, so think about
how you store state.

### What to implement

`class Keyboard`:

- `Keyboard()` starts with an empty buffer.
- `type(s: str) -> None`: append `s` to the end of the buffer. `s` can be
  any length, including empty.
- `backspace(n: int = 1) -> None`: remove the last `n` characters. If the
  buffer has fewer than `n`, remove everything that is there. Never raise.
- `text() -> str`: the current buffer.

### Worked example

```python
kb = Keyboard()
kb.type("hello")
kb.type(" world")
kb.backspace(3)
kb.text()          # -> "hello wo"
kb.backspace(100)
kb.text()          # -> ""
```

### Clarifications

- **`backspace()` on an empty buffer?** Does nothing.
- **`backspace(0)`?** Does nothing.
- **`type("")`?** Does nothing visible. (In Part 2 it matters that this is a
  no-op.)
- **Are two `Keyboard` instances independent?** Yes. Do not use class-level
  or module-level state.
- **Any size or performance constraints?** Not in this part. A few thousand
  operations at most.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

Glassdoor lists "Implement a keyboard object with expansion to support
undo/redo operations" for a Staff Software Engineer loop; only the title
is public, so Parts 2 and 3 are reconstructions in the "requirements
expand onto your existing class" style Sierra candidates describe. Part 1
is a warm-up; the design question is how state is stored so that Part 2
is cheap.
