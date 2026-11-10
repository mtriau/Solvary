def all_passed(scores: list[int], threshold: int) -> bool:
    """Every score >= threshold (True for no scores)."""
    raise NotImplementedError


def any_failed(scores: list[int], threshold: int) -> bool:
    """Some score < threshold (False for no scores)."""
    raise NotImplementedError
