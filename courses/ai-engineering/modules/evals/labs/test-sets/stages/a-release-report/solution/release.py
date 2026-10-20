"""The help desk's report of a release on its test set."""

import math
from dataclasses import dataclass

import numpy as np

from checks import Checks
from margin import clustered_standard_error, margin


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
    reach = margin(clustered_standard_error(scores, pages), confidence)
    return Line(
        rate=float(scores.mean()),
        margin=reach,
        questions=len(scores),
        needed=math.ceil(len(scores) * (reach / target) ** 2),
    )


def report(
    results: dict[str, Checks],
    pages: dict[str, str],
    services: dict[str, str],
    target: float,
    confidence: float,
) -> dict[str, Line]:
    """A line for every question, as `all`, and one for each service, in alphabetical
    order."""
    names = list(results)
    scores = np.array([float(all(results[name].values())) for name in names])
    lines = {"all": line(scores, [pages[name] for name in names], target, confidence)}
    for service in sorted({services[name] for name in names}):
        theirs = [
            index for index, name in enumerate(names) if services[name] == service
        ]
        theirs_pages = [pages[names[index]] for index in theirs]
        lines[service] = line(scores[theirs], theirs_pages, target, confidence)
    return lines
