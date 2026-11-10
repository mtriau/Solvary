import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def distance_to(self, other: "Point") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)
