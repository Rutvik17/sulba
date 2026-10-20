"""A search's chunks scored by the characters of a question's answer they hold. Each
part of an answer, and each chunk, is a place: its page, its first character and the one
after its last."""

type Place = tuple[str, int, int]


def held(parts: list[Place], found: list[Place]) -> int:
    """The answer's characters that one or more of the chunks found hold."""
    return sum(
        any(page == chunk and start <= at < end for chunk, start, end in found)
        for page, first, last in parts
        for at in range(first, last)
    )


def size(places: list[Place]) -> int:
    """The places' characters, a character in two places counted twice."""
    return sum(end - start for _, start, end in places)


def recall(parts: list[Place], found: list[Place]) -> float:
    """The share of the answer's characters that the chunks found hold."""
    return held(parts, found) / size(parts)


def precision(parts: list[Place], found: list[Place]) -> float:
    """The share of the found chunks' characters that are the answer's; 0.0 when nothing
    is found."""
    return held(parts, found) / size(found) if found else 0.0


def iou(parts: list[Place], found: list[Place]) -> float:
    """The answer's characters the chunks hold, over the answer's and the chunks' less
    those."""
    shared = held(parts, found)
    return shared / (size(parts) + size(found) - shared)


def holding(parts: list[Place], chunks: list[Place]) -> list[Place]:
    """The chunks that hold one or more of the answer's characters, in their order."""
    return [
        (page, start, end)
        for page, start, end in chunks
        if any(page == at and start < last and first < end for at, first, last in parts)
    ]
