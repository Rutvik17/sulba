"""The help desk's chunker, for each page it adds or changes: the page cut between its
blocks into chunks of at most 100 words, each heading starting a new chunk, each chunk
as its place in the page."""


def chunks(text: str) -> list[tuple[int, int]]:
    """Each chunk's first character and the one after its last."""
    raise NotImplementedError
