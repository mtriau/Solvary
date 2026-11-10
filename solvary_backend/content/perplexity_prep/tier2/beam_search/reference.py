"""Reference: beam search.

beams = [(score, seq, finished)]. Each step: finished beams carry over as
candidates (in beam order), then every live beam is expanded via `step(seq)`
(candidates in beam order, then step-list order). Keep the `beam_width`
best by score; ties go to the lower candidate index. A beam that emits
`eos`, or whose `step` returns nothing, is finished and keeps its slot.
Stop when no live beams remain or `max_len` tokens have been appended.

Complexity: O(max_len * B * K * log B) with B = beam_width and K = the
largest step() list (heapq.nlargest over B*K candidates per step).
Sequences are tuples: every extension builds a new tuple.
"""

import heapq
from typing import Callable


def beam_search(step: Callable[[tuple], list[tuple[str, float]]], start: tuple,
                beam_width: int, max_len: int, eos: str) -> list[tuple[tuple, float]]:
    """Keep the beam_width best partial sequences per step. See PROBLEMS.md #2."""
    beams: list[tuple[float, tuple, bool]] = [(0.0, tuple(start), False)]
    for _ in range(max_len):
        if all(finished for _, _, finished in beams):
            break
        candidates: list[tuple[float, tuple, bool]] = [b for b in beams if b[2]]
        for score, seq, finished in beams:
            if finished:
                continue
            expansions = step(seq)
            if not expansions:
                candidates.append((score, seq, True))     # nothing to extend with: done as is
                continue
            for token, logprob in expansions:
                candidates.append((score + logprob, seq + (token,), token == eos))
        # Highest score first; on a tie the earlier candidate (lower index) wins.
        best = heapq.nlargest(beam_width, enumerate(candidates),
                              key=lambda ic: (ic[1][0], -ic[0]))
        beams = [cand for _, cand in best]
    ordered = sorted(beams, key=lambda b: -b[0])          # stable: tie order preserved
    return [(seq, score) for score, seq, _ in ordered]
