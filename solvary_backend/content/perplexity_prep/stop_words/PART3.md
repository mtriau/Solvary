# Stop Words: Part 3 (reveal verbatim)

Now the text arrives as arbitrary string chunks and you must emit output as
early as possible. Implement `StopStream(stop_words: list[str])` with
`feed(chunk: str) -> str`: returns the text that can now be safely emitted
(text that cannot be part of a stop word that is still completing). A stop
word may span chunk boundaries.

Precisely, after appending the chunk to what has been buffered:

- If a stop word now occurs in the buffered text, return everything before
  its earliest occurrence that has not been returned yet; then ignore all
  further input (every later `feed` returns `""`).
- Otherwise withhold the longest suffix of the buffer that is a proper
  prefix of some stop word (at most max stop word length minus 1
  characters) and return the rest.
- An empty chunk returns `""`. Empty-string stop words are ignored.

The concatenation of every return value equals
`text_before_stop(concatenated input, stop_words)`.

Example with `["fox"]`: `feed("the quick brown fo")` returns
`"the quick brown "` (the `"fo"` could be the start of `"fox"`); then
`feed("x jumps")` returns `""`, and `feed("more")` returns `""`.

Provided tests: `test_stop_words_p3.py` (copy into `stop_words/`), then
`pytest stop_words -q`.
