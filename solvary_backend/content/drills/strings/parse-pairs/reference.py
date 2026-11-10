def parse_pairs(text: str) -> dict[str, int]:
    pairs = {}
    for item in text.split(";"):
        if not item.strip():
            continue
        key, _, value = item.partition("=")
        pairs[key.strip()] = int(value)
    return pairs
