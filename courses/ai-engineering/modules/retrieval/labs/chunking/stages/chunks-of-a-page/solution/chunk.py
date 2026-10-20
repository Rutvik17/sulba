"""A page's text cut into chunks, windows of words or its blocks joined, each as its
place in the text."""

import re

# A word is a run of characters other than space, and a block is lines with no blank
# line between them.
WORD = re.compile(r"\S+")
BLOCK = re.compile(r"[^\n]+(?:\n(?!\n)[^\n]+)*")


def words(text: str) -> list[tuple[int, int]]:
    """Each word's first character and the one after its last."""
    return [match.span() for match in WORD.finditer(text)]


def windows(text: str, size: int, overlap: int = 0) -> list[tuple[int, int]]:
    """The text in windows of size words, each starting size - overlap words after the
    one before, and the last ending at the text's last word."""
    if not 0 <= overlap < size:
        raise ValueError(
            f"An overlap of {overlap} needs windows of more than {overlap} words."
        )
    places = words(text)
    found = []
    for first in range(0, len(places), size - overlap):
        last = min(first + size, len(places)) - 1
        found.append((places[first][0], places[last][1]))
        if last == len(places) - 1:
            break
    return found


def blocks(text: str) -> list[tuple[int, int]]:
    """Each block's first character and the one after its last."""
    return [match.span() for match in BLOCK.finditer(text)]


def joined(text: str, most: int) -> list[tuple[int, int]]:
    """The blocks joined in order until another would take a chunk past most words; a
    block of more than most words is a chunk of its own."""
    found: list[tuple[int, int, int]] = []
    for start, end in blocks(text):
        size = len(text[start:end].split())
        if found and found[-1][2] + size <= most:
            found[-1] = (found[-1][0], end, found[-1][2] + size)
        else:
            found.append((start, end, size))
    return [(start, end) for start, end, _ in found]
