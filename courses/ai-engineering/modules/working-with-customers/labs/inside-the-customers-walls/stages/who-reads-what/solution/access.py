"""The office's staff guidance, each document for the groups that may read it, and a search that
finds only what the person searching may read."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """A document of the office's: its id, title and text, and the groups that may read it."""

    id: str
    title: str
    text: str
    groups: frozenset[str]


# The office's guidance for its staff, as its document store holds it.
DOCUMENTS = [
    Document(
        "d1",
        "Opening a benefits claim",
        "Check the caller's identity first, then open the claim and give them its number.",
        frozenset({"benefits"}),
    ),
    Document(
        "d2",
        "Overpayment letters",
        "The letter gives the amount overpaid and how to repay it. Supervisors can agree a"
        " repayment plan.",
        frozenset({"benefits", "supervisors"}),
    ),
    Document(
        "d3",
        "Agreeing a repayment plan",
        "Supervisors agree repayment plans of up to 24 months. Longer plans go to the county's"
        " finance team.",
        frozenset({"supervisors"}),
    ),
    Document(
        "d4",
        "New veterans' claims",
        "Book the veterans' adviser, who is in on Tuesdays and Thursdays, for a new claim.",
        frozenset({"veterans"}),
    ),
    Document(
        "d5",
        "Callers in distress",
        "Stay on the line, and transfer the caller to the county's crisis line if they ask or"
        " are at risk.",
        frozenset({"benefits", "veterans", "front-desk"}),
    ),
    Document(
        "d6",
        "Opening the front desk",
        "Open the doors at 8:30, and check that the queue screens are on.",
        frozenset({"front-desk"}),
    ),
    Document(
        "d7",
        "Open discipline cases",
        "Only supervisors read open cases, and never discuss them on the phone.",
        frozenset({"supervisors"}),
    ),
    Document(
        "d8",
        "Draft: the new phone menu",
        "Not yet agreed: callers would choose their service before their language.",
        frozenset(),
    ),
]


def readable(documents: list[Document], groups: frozenset[str]) -> list[Document]:
    """The documents someone in the groups may read, in order: those that name one of their
    groups. A document that names no group is for no one."""
    return [document for document in documents if document.groups & groups]


def words(text: str) -> set[str]:
    """The text's words in lower case, without punctuation, of four letters or more."""
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= 4}


def search(
    question: str, documents: list[Document], groups: frozenset[str], k: int = 3
) -> list[Document]:
    """The k documents someone in the groups may read that share the most words with the
    question, of those that share any, the earlier first on a tie."""
    asked = words(question)
    scored = [
        (len(asked & words(f"{document.title} {document.text}")), document)
        for document in readable(documents, groups)
    ]
    ranked = sorted((pair for pair in scored if pair[0] > 0), key=lambda pair: -pair[0])
    return [document for _, document in ranked[:k]]
