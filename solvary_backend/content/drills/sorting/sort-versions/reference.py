def sort_versions(versions: list[str]) -> list[str]:
    return sorted(versions, key=lambda v: tuple(int(part) for part in v.split(".")))
