from dataclasses import dataclass

MODEL = "Qwen3.5-0.8B"
STAFF = "I'll pass your question to the aid office's staff, who will reply by email."
INSTRUCTIONS = (
    "You answer students' questions for Harbor College's aid office, from the numbered "
    "passages of Federal Student Aid's pages that come with each question, and from nothing "
    "else. Cite each passage you use by its number in brackets, such as [2]. If the passages "
    "don't answer the question, reply only: I don't know."
)
MAX_TOKENS = 300
TIMEOUT = 60


@dataclass(frozen=True)
class Answer:
    text: str
    pages: list[str]
    to_staff: bool


def cited(reply, pages):
    """The pages a reply cites, by the numbers of the passages it was given, from [1], in
    the order it first cites them, each once. A number that names no passage is left out."""
    raise NotImplementedError


def answer(conn, client, question):
    """The model's answer from the office's pages, with the pages it cites, or the question
    passed to staff: when the search finds no page, without asking the model, and when the
    model says it doesn't know, cites nothing or doesn't reply."""
    raise NotImplementedError
