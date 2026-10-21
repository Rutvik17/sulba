"""Replies on the help desk's pages whose verdict is known."""

import numpy as np


def own(
    question: dict[str, str], relevant: list[str], passages: dict[str, dict[str, str]]
) -> list[str]:
    """The passages that hold the question's answer on its own page, in the order given."""
    raise NotImplementedError


def partners(questions: list[dict[str, str]]) -> dict[str, str]:
    """Each question's partner from another service: the question half the list further on,
    going round from the end to the start, or the first after it from another service."""
    raise NotImplementedError


def error_rates(labels: np.ndarray, verdicts: np.ndarray) -> tuple[float, float]:
    """The share of the replies labelled 1 that the grader calls 0, its misses, and the share
    of those labelled 0 that it calls 1, its false alarms."""
    raise NotImplementedError
