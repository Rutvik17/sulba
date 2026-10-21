"""The help desk's report of how many of a release's replies keep to their passages."""

from dataclasses import dataclass

import httpx
import jinja2
import numpy as np


@dataclass(frozen=True)
class Line:
    """One line of the report: the share of the replies the grader calls ungrounded, its
    margin of error, and how many replies it rests on."""

    flagged: float
    margin: float
    replies: int


def shown(names: list[str], passages: dict[str, dict[str, str]]) -> str:
    """The passages as the help desk shows them: each as its name in square brackets and
    its page's title, then its text on the next line, with a blank line between them."""
    raise NotImplementedError


def risks(
    client: httpx.Client,
    chat: jinja2.Template,
    replies: dict[str, str],
    passages: dict[str, dict[str, str]],
    ranked: dict[str, list[str]],
    today: str,
) -> dict[str, float]:
    """The grader's risk for each question's reply, with the passages the help desk showed
    with the question."""
    raise NotImplementedError


def line(flags: np.ndarray, pages: list[str], confidence: float) -> Line:
    """The line for a group of replies, from their flags, 1 for a reply the grader calls
    ungrounded and 0 for one it doesn't, each page's replies counted together."""
    raise NotImplementedError


def report(
    risks: dict[str, float],
    questions: dict[str, dict[str, str]],
    threshold: float,
    confidence: float,
) -> dict[str, Line]:
    """A line for every reply, as `all`, then one for each service in alphabetical
    order."""
    raise NotImplementedError


def to_read(risks: dict[str, float], threshold: float) -> list[str]:
    """The questions whose replies the grader calls ungrounded, the likeliest first, and in
    their order where two tie."""
    raise NotImplementedError
