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
    raise NotImplementedError


def split(
    questions: list[Question], share: float, rng: np.random.Generator
) -> tuple[list[str], list[str]]:
    """The ids of the unique questions, in order, as a development set and a test set that
    share no page and hold at least `share` of each service's questions."""
    raise NotImplementedError
