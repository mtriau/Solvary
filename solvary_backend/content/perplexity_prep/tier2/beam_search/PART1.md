# Beam search

```python
def beam_search(step, start: tuple, beam_width: int, max_len: int, eos) -> list[tuple[tuple, float]]
```

`step(seq) -> list[(token, logprob)]` gives the next-token distribution
for a sequence. Starting from `start`, keep the `beam_width` highest-scoring
partial sequences (score = sum of logprobs) at every step. A sequence that
emits `eos` is finished and no longer extended. Stop after `max_len` tokens
have been appended or when no live beams remain. Return the finished (or
truncated) sequences sorted by score descending, at most `beam_width`.

```python
def step(seq):
    if len(seq) == 0: return [("a", -0.1), ("b", -2.0)]
    if seq[-1] == "a": return [("<eos>", -0.5), ("b", -0.3)]
    return [("<eos>", -0.1)]

beam_search(step, (), beam_width=2, max_len=3, eos="<eos>")
# -> [(("a", "b", "<eos>"), -0.5), (("a", "<eos>"), -0.6)]
```

A finished sequence keeps occupying one of the `beam_width` slots and
competes on score with live ones. Ties: lower index in the candidate list
wins. Use a heap; state complexity.

`beam_width=1` is greedy decoding. If `step` returns an empty list, that
sequence is finished as it stands (no `eos` appended). If `max_len` is
reached first, the unfinished sequences are returned as they stand. Scores
are sums of logprobs, never products.
