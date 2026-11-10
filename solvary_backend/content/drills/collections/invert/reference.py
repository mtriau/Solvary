def invert(mapping: dict[str, int]) -> dict[int, str]:
    return {value: key for key, value in mapping.items()}
