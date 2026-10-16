from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    width: float
    height: float


def area(box: Box) -> float:
    return box.width * box.height
