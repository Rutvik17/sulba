"""Replies on the help desk's pages whose verdict is known."""

import numpy as np


def own(
    question: dict[str, str], relevant: list[str], passages: dict[str, dict[str, str]]
) -> list[str]:
    """The passages that hold the question's answer on its own page, in the order given."""
    return [name for name in relevant if passages[name]["page"] == question["page"]]


def partners(questions: list[dict[str, str]]) -> dict[str, str]:
    """Each question's partner from another service: the question half the list further on,
    going round from the end to the start, or the first after it from another service."""
    found = {}
    for index, question in enumerate(questions):
        start = (index + len(questions) // 2) % len(questions)
        found[question["question"]] = next(
            other["question"]
            for other in questions[start:] + questions[:start]
            if other["domain"] != question["domain"]
        )
    return found


def error_rates(labels: np.ndarray, verdicts: np.ndarray) -> tuple[float, float]:
    """The share of the replies labelled 1 that the grader calls 0, its misses, and the share
    of those labelled 0 that it calls 1, its false alarms."""
    misses = float(np.mean(verdicts[labels == 1] == 0))
    false_alarms = float(np.mean(verdicts[labels == 0] == 1))
    return misses, false_alarms
