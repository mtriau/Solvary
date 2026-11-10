# Stop Words: Part 1

Implement `text_before_stop(text: str, stop_words: list[str]) -> str`.

Return the portion of `text` that comes **before the first occurrence** of
any stop word. Stop words match as exact, case-sensitive **substrings**
(not whole words). If no stop word occurs, return the whole text.

```python
text_before_stop("the quick brown fox jumps", ["fox", "jumps"])  # -> "the quick brown "
text_before_stop("hello world", ["xyz"])                          # -> "hello world"
text_before_stop("stop now", ["stop"])                            # -> ""
text_before_stop("a cat sat", ["sat", "cat"])                     # -> "a "
text_before_stop("bananas", ["nan", "ana"])                       # -> "b"
```

Contract: an empty text returns `""`; an empty stop-word list returns the
whole text; empty-string stop words are ignored. Run the provided tests:
`pytest stop_words -q`. Later parts come with their own test files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*
