"""The help desk's questions split into a development set and a test set."""

import re

import numpy as np

WORD = re.compile(r"\w+")

Question = dict[str, str]


def words(text: str) -> tuple[str, ...]:
    """A question's words, lowercased, each a run of letters, digits and underscores."""
    return tuple(WORD.findall(text.lower()))


def unique(questions: list[Question]) -> list[Question]:
    """The questions in order, each one with the same words as an earlier one left out."""
    seen: set[tuple[str, ...]] = set()
    kept = []
    for question in questions:
        key = words(question["text"])
        if key not in seen:
            seen.add(key)
            kept.append(question)
    return kept


def split(
    questions: list[Question], share: float, rng: np.random.Generator
) -> tuple[list[str], list[str]]:
    """The ids of the unique questions, in order, as a development set and a test set that
    share no page and hold at least `share` of each service's questions."""
    kept = unique(questions)
    test: set[str] = set()
    for service in sorted({question["domain"] for question in kept}):
        theirs = [question for question in kept if question["domain"] == service]
        pages = list(dict.fromkeys(question["page"] for question in theirs))
        held = 0
        for index in rng.permutation(len(pages)):
            if held >= share * len(theirs):
                break
            on_page = [q["question"] for q in theirs if q["page"] == pages[index]]
            test.update(on_page)
            held += len(on_page)
    development = [q["question"] for q in kept if q["question"] not in test]
    return development, [q["question"] for q in kept if q["question"] in test]
