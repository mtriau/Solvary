def top_scores(scores: dict[str, int], n: int) -> list[str]:
    return sorted(scores, key=lambda name: (-scores[name], name))[:n]
