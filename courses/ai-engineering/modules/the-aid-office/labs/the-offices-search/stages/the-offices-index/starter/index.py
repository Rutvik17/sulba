from dataclasses import dataclass

EMBEDDER = "nomic-embed-text-v1.5"
DOCUMENT = "search_document: "
BATCH = 32


@dataclass(frozen=True)
class Passage:
    id: str
    page: str
    title: str
    text: str


def read(path):
    """The passages in the file at path, in order."""
    raise NotImplementedError


def connect(url):
    raise NotImplementedError


def create(conn):
    raise NotImplementedError


def sync(conn, client, passages):
    """Make the table hold the passages: the ones it lacks added, the rest removed, and only the
    new and changed texts embedded. Gives the ids of the passages embedded, in order."""
    raise NotImplementedError
