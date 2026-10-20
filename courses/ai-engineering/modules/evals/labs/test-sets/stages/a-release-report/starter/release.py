"""The help desk's report of a release on its test set."""

from dataclasses import dataclass

import numpy as np

from checks import Checks


@dataclass(frozen=True)
class Line:
    """One line of the report: the share of the replies that pass every check, its margin
    of error, the questions it rests on, and the questions a test set like this one would
    need for the margin the help desk wants."""

    rate: float
    margin: float
    questions: int
    needed: int


def line(
    scores: np.ndarray, pages: list[str], target: float, confidence: float
) -> Line:
    """The line for a group of questions' scores, each page's questions counted together."""
    raise NotImplementedError


def report(
    results: dict[str, Checks],
    pages: dict[str, str],
    services: dict[str, str],
    target: float,
    confidence: float,
) -> dict[str, Line]:
    """A line for every question, as `all`, and one for each service, in alphabetical
    order."""
    raise NotImplementedError
