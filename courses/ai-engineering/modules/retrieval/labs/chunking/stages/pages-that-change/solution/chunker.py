"""The help desk's chunker, for each page it adds or changes: the page cut between its
blocks into chunks of at most 100 words, each heading starting a new chunk, each chunk
as its place in the page."""

import re

MOST = 100
WORD = re.compile(r"\S+")
# A blank line holds nothing but spaces, tabs or a carriage return.
BLANK = re.compile(r"\n[^\S\n]*\n")


def blocks(text: str) -> list[tuple[int, int, int]]:
    """Each block's first character other than space, the one after its last, and its
    words."""
    found = []
    start = 0
    for blank in [*BLANK.finditer(text), None]:
        end = blank.start() if blank else len(text)
        words = [match.span() for match in WORD.finditer(text, start, end)]
        if words:
            found.append((words[0][0], words[-1][1], len(words)))
        start = blank.end() if blank else end
    return found


def chunks(text: str) -> list[tuple[int, int]]:
    """Each chunk's first character and the one after its last."""
    found: list[list[int]] = []
    headings = False  # whether the last chunk holds only headings
    for start, end, size in blocks(text):
        heading = text[start] == "#"
        if size > MOST:
            words = [match.span() for match in WORD.finditer(text, start, end)]
            for first in range(0, size, MOST):
                window = words[first : first + MOST]
                # No block joins a window.
                found.append([window[0][0], window[-1][1], MOST])
            headings = False
        elif found and found[-1][2] + size <= MOST and (headings or not heading):
            found[-1][1:] = [end, found[-1][2] + size]
            headings = headings and heading
        else:
            found.append([start, end, size])
            headings = heading
    return [(start, end) for start, end, _ in found]
