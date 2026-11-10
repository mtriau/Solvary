# Stop Words: Part 2 (reveal verbatim)

Now tokens arrive one at a time. Implement `TokenStream(stop_words:
set[str], window: int)`:

- `push(token: str) -> None`: ignore the token if it is a stop word (exact
  whole-token match now); otherwise it enters the window. The window holds
  the most recent `window` non-stop tokens; older ones fall out. A stop
  word never evicts anything.
- `counts() -> dict[str, int]`: frequency of each token currently in the
  window (no zero entries).
- `top_k(k: int) -> list[str]`: the k most frequent tokens in the window,
  by count descending, ties broken alphabetically; fewer than k if the
  window has fewer distinct tokens.

Memory must stay O(window) no matter how many tokens are pushed.

Provided tests: `test_stop_words_p2.py` (copy into `stop_words/`), then
`pytest stop_words -q`.
