"""Grades replies with Granite Guardian, at the threshold BEGIN chooses."""

import httpx
import jinja2
import numpy as np

from agreement import best_threshold, kappa
from grader import prompt, risk

# The most of a context a prompt holds, in characters, so that it fits in the grader's 4,096
# tokens.
LONGEST = 4000


def graded(
    client: httpx.Client, chat: jinja2.Template, items: list[dict[str, str]], today: str
) -> list[float]:
    """The grader's risk for each item, a context and a reply, in order. A reply already
    graded isn't sent again, and a request that fails counts as grounded, so that one failure
    doesn't stop a run of thousands."""
    scores: dict[str, float] = {}
    keys = [item["reply"] for item in items]
    for key, item in zip(keys, items, strict=True):
        if key not in scores:
            text = prompt(chat, item["context"][:LONGEST], item["reply"], today)
            try:
                scores[key] = risk(client, text)
            except httpx.HTTPStatusError:
                scores[key] = 0.0
    return [scores[key] for key in keys]


def labelled(
    begin: list[dict[str, str]], risks: dict[str, float], sets: tuple[str, ...]
) -> tuple[np.ndarray, np.ndarray]:
    """The people's labels, 1 where a reply says something its text doesn't, and the
    grader's risks, for BEGIN's replies in the sets named."""
    rows = [row for row in begin if row["set"] in sets]
    labels = np.array([row["label"] != "Fully attributable" for row in rows], dtype=int)
    return labels, np.array([risks[row["item"]] for row in rows])


def chosen(begin: list[dict[str, str]], risks: dict[str, float]) -> float:
    """The threshold that gives the highest kappa on BEGIN's test set, the replies its
    agreement is reported on."""
    return best_threshold(*labelled(begin, risks, ("test",)))


def agreement(
    begin: list[dict[str, str]], risks: dict[str, float], threshold: float
) -> float:
    """The grader's kappa with people on BEGIN's test set, at the threshold."""
    labels, scores = labelled(begin, risks, ("test",))
    return kappa(labels, (scores >= threshold).astype(int))


def flagged(scores: list[float], threshold: float) -> float:
    """The share of the replies the grader calls ungrounded."""
    return float(np.mean(np.array(scores) >= threshold))
