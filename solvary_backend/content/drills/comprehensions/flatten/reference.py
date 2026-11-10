def flatten(rows: list[list[int]]) -> list[int]:
    return [x for row in rows for x in row]
