from dataclasses import dataclass

MODEL = "Qwen3.5-0.8B"
WORDS = 200
BEST = 5
STAFF = "I'll pass your question to the aid office's staff, who will reply by email."
INSTRUCTIONS = (
    "You answer students' questions for Harbor College's aid office, from the numbered "
    "passages of Federal Student Aid's pages that come with each question, and from nothing "
    "else. Cite each passage you use by its number in brackets, such as [2]. If the passages "
    "don't answer the question, reply only: I don't know."
)


@dataclass(frozen=True)
class Passage:
    page: str
    title: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    pages: list[str]
    to_staff: bool


def passages(path):
    """The pages' passages, in order: each page's blocks, which a blank line divides, joined
    until another would take a passage past WORDS words."""
    raise NotImplementedError


class Search:
    """A search over the passages, built once."""

    def __init__(self, passages):
        raise NotImplementedError

    def best(self, question, k):
        """The k passages that best answer the question, best first, none that shares no word
        with it."""
        raise NotImplementedError


def answer(client, search, question):
    """The model's answer from the question's best passages, with the pages it cites, or the
    question passed to staff when there's nothing to answer from, the model can't answer, or its
    reply cites nothing."""
    raise NotImplementedError
