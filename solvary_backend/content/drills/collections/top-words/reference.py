from collections import Counter


def top_words(text: str, n: int) -> list[tuple[str, int]]:
    return Counter(text.lower().split()).most_common(n)
