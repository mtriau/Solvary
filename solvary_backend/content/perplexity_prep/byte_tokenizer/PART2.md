# Byte Tokenizer: Part 2 (reveal verbatim)

Interviewer: after Part 1 is green, read the block below to the candidate, then
copy `_interviewer/tests/byte_tokenizer/test_byte_tokenizer_p2.py` into
`byte_tokenizer/` and have them run `pytest byte_tokenizer -q`.

---

Part 2: detokenize, and make it fast.

- You will tokenize millions of short strings against the SAME alphabet
  (around 50K entries). Restructure so the per-string cost does not scale
  with the alphabet size. Build a `Tokenizer(alphabet)` class once from the
  alphabet.
- `Tokenizer.tokenize(text) -> list[int]`: identical output to the Part 1
  function on every input (keep the Part 1 function; the tests compare the
  two). Return a fresh list on every call.
- `Tokenizer.detokenize(ids) -> str`: inverse of tokenize. An invalid id
  (out of range, including negative) raises ValueError.
- Performance target in the tests: a 50,000-entry alphabet (256 single
  characters, then multi-character tokens built by concatenating two earlier
  tokens); tokenizing 2,000 random strings of 5 to 20 characters must finish
  in under 3 seconds, and must match the Part 1 function on a sample of them.

---

Interviewer notes (do not read aloud):
- Expected ideas (any two is strong): precompute `pair_to_id` /
  `rank[id]` once and only run passes for tokens that occur; a substring
  pre-filter (`tok in text`, or enumerate substrings of the text up to the
  longest token length and look them up); an LRU cache keyed by text.
- Make them argue equivalence: a pass for an absent token is a no-op, and
  present tokens are still applied in alphabet order. Do not accept "it is
  basically BPE" without the "aaa" check
  (`test_class_single_pass_does_not_rescan_new_token`).
- Watch for a shared cached list leaking out
  (`test_class_tokenize_returns_a_fresh_list_each_call`) and for
  `alphabet[-1]` silently accepting a negative id in detokenize.
