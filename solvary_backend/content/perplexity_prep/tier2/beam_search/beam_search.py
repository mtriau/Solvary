from typing import Callable


def beam_search(step: Callable[[tuple], list[tuple[str, float]]], start: tuple,
                beam_width: int, max_len: int, eos: str) -> list[tuple[tuple, float]]:
    """Keep the beam_width best partial sequences per step. See PROBLEMS.md #2."""
    raise NotImplementedError
