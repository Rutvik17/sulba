"""Grades replies with Granite Guardian, at the threshold BEGIN's development set chooses."""

import httpx
import jinja2
import numpy as np

from agreement import best_threshold, kappa
from grader import prompt, risk


def graded(
    client: httpx.Client, chat: jinja2.Template, items: list[dict[str, str]], today: str
) -> list[float]:
    """The grader's risk for each item, a context and a reply, in order. An item with the
    same context and reply as one already graded isn't sent again, and a request the server
    refuses raises."""
    scores: dict[tuple[str, str], float] = {}
    keys = [(item["context"], item["reply"]) for item in items]
    for context, reply in keys:
        if (context, reply) not in scores:
            scores[context, reply] = risk(client, prompt(chat, context, reply, today))
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
    """The threshold that gives the highest kappa on BEGIN's development set."""
    return best_threshold(*labelled(begin, risks, ("dev",)))


def agreement(
    begin: list[dict[str, str]], risks: dict[str, float], threshold: float
) -> float:
    """The grader's kappa with people on BEGIN's test set, at the threshold."""
    labels, scores = labelled(begin, risks, ("test",))
    return kappa(labels, (scores >= threshold).astype(int))


def flagged(scores: list[float], threshold: float) -> float:
    """The share of the replies the grader calls ungrounded."""
    return float(np.mean(np.array(scores) >= threshold))
