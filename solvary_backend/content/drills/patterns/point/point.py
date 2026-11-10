class Point:
    """Immutable 2-D point with value semantics."""

    def __init__(self, x: int, y: int) -> None:
        raise NotImplementedError

    def distance_to(self, other: "Point") -> float:
        raise NotImplementedError
