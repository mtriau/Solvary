def parse_ints(text: str) -> list[int]:
    return [
        int(line)
        for raw in text.splitlines()
        if (line := raw.strip()) and not line.startswith("#")
    ]
