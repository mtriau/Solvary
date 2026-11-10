def initials(names: list[str]) -> set[str]:
    return {name.strip()[0].upper() for name in names if name.strip()}
