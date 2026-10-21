"""The help desk's report of how many of a release's replies keep to their passages."""

import math
from collections import defaultdict
from dataclasses import dataclass
from statistics import NormalDist

import httpx
import jinja2
import numpy as np

from judge import graded

# How many of the passages the search ranks first the help desk shows with a question.
SHOWN = 5


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
    return "\n\n".join(
        f"[{name}] {passages[name]['title']}\n{passages[name]['text']}"
        for name in names
    )


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
    names = list(replies)
    items = [
        {"context": shown(ranked[name][:SHOWN], passages), "reply": replies[name]}
        for name in names
    ]
    return dict(zip(names, graded(client, chat, items, today), strict=True))


def line(flags: np.ndarray, pages: list[str], confidence: float) -> Line:
    """The line for a group of replies, from their flags, 1 for a reply the grader calls
    ungrounded and 0 for one it doesn't, each page's replies counted together."""
    sums: dict[str, float] = defaultdict(float)
    for page, error in zip(pages, flags - flags.mean(), strict=True):
        sums[page] += error
    groups = len(sums)
    spread = math.sqrt(groups / (groups - 1) * sum(total**2 for total in sums.values()))
    reach = NormalDist().inv_cdf((1 + confidence) / 2) * spread / len(flags)
    return Line(flagged=float(flags.mean()), margin=reach, replies=len(flags))


def report(
    risks: dict[str, float],
    questions: dict[str, dict[str, str]],
    threshold: float,
    confidence: float,
) -> dict[str, Line]:
    """A line for every reply, as `all`, then one for each service in alphabetical
    order."""
    names = list(risks)
    flags = np.array([float(risks[name] >= threshold) for name in names])
    pages = [questions[name]["page"] for name in names]
    lines = {"all": line(flags, pages, confidence)}
    for service in sorted({questions[name]["domain"] for name in names}):
        theirs = [
            i for i, name in enumerate(names) if questions[name]["domain"] == service
        ]
        lines[service] = line(flags[theirs], [pages[i] for i in theirs], confidence)
    return lines


def to_read(risks: dict[str, float], threshold: float) -> list[str]:
    """The questions whose replies the grader calls ungrounded, the likeliest first, and in
    their order where two tie."""
    flagged = [name for name in risks if risks[name] >= threshold]
    return sorted(flagged, key=lambda name: -risks[name])
