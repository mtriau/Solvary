# Byte Tokenizer: Part 3 (reveal verbatim)

Interviewer: after Part 2 is green, read the block below to the candidate, then
copy `_interviewer/tests/byte_tokenizer/test_byte_tokenizer_p3.py` into
`byte_tokenizer/` and have them run `pytest byte_tokenizer -q`.

---

Part 3: count and stream.

- `Tokenizer.count_tokens(text) -> int` for billing estimates: it must equal
  `len(tokenize(text))`. Can you do better than tokenizing? (Say what is
  exact and what is an approximation.)
- Very long texts: `Tokenizer.tokenize_long(text) -> list[int]` must equal
  `tokenize(text)` but may tokenize in chunks. Can you tokenize in chunks?
  Only if no multi-character token spans a chunk boundary; splitting at
  whitespace is safe iff no token contains whitespace. State the assumption
  and, when the alphabet does have a token containing whitespace, fall back
  to plain tokenization. Whitespace characters are tokens too and stay in
  the output. The tests run a 200,000-character whitespace-separated text
  and expect it in under 3 seconds.

---

Interviewer notes (do not read aloud):
- Honest answer on count_tokens: not exactly, unless you tokenize;
  approximations by bytes-per-token ratio are fine if labeled as such. A
  strong answer: tokenize, since it is now cheap, and cache.
- The fallback probes are
  `test_tokenize_long_falls_back_when_a_token_contains_a_space` and
  `..._spans_a_word_boundary`; candidates who split at spaces without
  checking the alphabet fail both.
