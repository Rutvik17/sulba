"""A page's text cut into chunks, windows of words or its blocks joined, each as its
place in the text."""


def words(text: str) -> list[tuple[int, int]]:
    """Each word's first character and the one after its last."""
    raise NotImplementedError


def windows(text: str, size: int, overlap: int = 0) -> list[tuple[int, int]]:
    """The text in windows of size words, each starting size - overlap words after the
    one before, and the last ending at the text's last word."""
    raise NotImplementedError


def blocks(text: str) -> list[tuple[int, int]]:
    """Each block's first character and the one after its last."""
    raise NotImplementedError


def joined(text: str, most: int) -> list[tuple[int, int]]:
    """The blocks joined in order until another would take a chunk past most words; a
    block of more than most words is a chunk of its own."""
    raise NotImplementedError
