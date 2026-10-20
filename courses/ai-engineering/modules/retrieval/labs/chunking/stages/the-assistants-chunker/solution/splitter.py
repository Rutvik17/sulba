"""The help desk's chunker: each page's blocks joined into chunks of at most a number of
words, and each chunk's place in the page."""

import re

WORD = re.compile(r"\S+")


def windows(block: str, most: int) -> list[str]:
    """A block's text in windows of most words."""
    words = [match.span() for match in WORD.finditer(block)]
    return [
        block[words[first][0] : words[min(first + most, len(words)) - 1][1]]
        for first in range(0, len(words), most)
    ]


def split(text: str, most: int) -> list[str]:
    """The page's blocks, a blank line apart, joined in order until another would take a
    chunk past most words. A block of more than most words is cut into windows of most
    words, each a chunk of its own."""
    chunks: list[str] = []
    current, count = "", 0
    for block in text.split("\n\n"):
        size = len(block.split())
        if current and count + size > most:
            chunks.append(current)
            current, count = "", 0
        if size > most:
            chunks.extend(windows(block, most))
        elif current:
            current += "\n\n" + block
            count += size
        else:
            current, count = block, size
    if current:
        chunks.append(current)
    return chunks


def places(text: str, chunks: list[str]) -> list[tuple[int, int]]:
    """Each chunk's first character in the page and the one after its last, the chunks
    following each other in the page, none sharing its text with another."""
    found = []
    end = 0
    for chunk in chunks:
        start = text.find(chunk, end)
        end = start + len(chunk)
        found.append((start, end))
    return found
