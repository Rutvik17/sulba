from dataclasses import dataclass

from answers import STAFF


@dataclass(frozen=True)
class Piece:
    text: str


@dataclass(frozen=True)
class Verdict:
    text: str
    pages: list[str]
    to_staff: bool


TO_STAFF = Verdict(STAFF, [], True)


def stream(conn, client, question):
    """The answer as the model writes it: a Piece for each piece of its text, then a Verdict,
    the answer with the pages it cites, or the question passed to staff, which takes the
    pieces' place."""
    raise NotImplementedError
