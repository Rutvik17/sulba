"""A search's chunks scored by the characters of a question's answer they hold. Each
part of an answer, and each chunk, is a place: its page, its first character and the one
after its last."""

type Place = tuple[str, int, int]


def recall(parts: list[Place], found: list[Place]) -> float:
    """The share of the answer's characters that the chunks found hold."""
    raise NotImplementedError


def precision(parts: list[Place], found: list[Place]) -> float:
    """The share of the found chunks' characters that are the answer's; 0.0 when nothing
    is found."""
    raise NotImplementedError


def iou(parts: list[Place], found: list[Place]) -> float:
    """The answer's characters the chunks hold, over the answer's and the chunks' less
    those."""
    raise NotImplementedError


def holding(parts: list[Place], chunks: list[Place]) -> list[Place]:
    """The chunks that hold one or more of the answer's characters, in their order."""
    raise NotImplementedError
