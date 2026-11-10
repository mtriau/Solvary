def all_passed(scores: list[int], threshold: int) -> bool:
    return all(score >= threshold for score in scores)


def any_failed(scores: list[int], threshold: int) -> bool:
    return any(score < threshold for score in scores)
