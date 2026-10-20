"""The help desk's test set, and its report of a release's pass rate on it."""

import numpy as np

from margin import clustered_standard_error, margin
from testset import words

Question = dict[str, str]


def held_out(
    questions: list[Question], share: float, rng: np.random.Generator
) -> list[str]:
    """The ids of the test set's questions, in order: each question with the words of an
    earlier one left out, and whole pages drawn from each service until the set holds at
    least `share` of the service's questions."""
    seen: set[tuple[str, ...]] = set()
    kept = []
    for question in questions:
        key = words(question["text"])
        if key not in seen:
            seen.add(key)
            kept.append(question)
    chosen: set[str] = set()
    for service in sorted({question["domain"] for question in kept}):
        theirs = [question for question in kept if question["domain"] == service]
        pages = list({question["page"] for question in theirs})
        held = 0
        for index in rng.permutation(len(pages)):
            for question in theirs:
                if question["page"] == pages[index] and held < share * len(kept):
                    chosen.add(question["question"])
                    held += 1
    return [question["question"] for question in kept if question["question"] in chosen]


def report(passed: dict[str, bool], pages: dict[str, str]) -> tuple[float, float]:
    """A release's pass rate on the test set, and its margin of error at 95%, each page's
    questions counted together."""
    names = list(passed)
    scores = np.array([float(passed[name]) for name in names])
    error = clustered_standard_error(scores, names)
    return float(scores.mean()), margin(error, 0.95)
