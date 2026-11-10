def longest_word(words: list[str]) -> str | None:
    return max(words, key=len, default=None)
