"""Measures of the passages a search shows for one question, and their mean over a run."""

import math
from collections.abc import Callable

Measure = Callable[[list[str | None], set[str], int], float]


def hit_rate(shown: list[str | None], relevant: set[str], k: int) -> float:
    """1 if a relevant passage is among the first k shown, else 0."""
    return 1.0 if any(passage in relevant for passage in shown[:k]) else 0.0


def recall(shown: list[str | None], relevant: set[str], k: int) -> float:
    """The share of the relevant passages that are among the first k shown, or 0 if no
    passage is relevant."""
    if not relevant:
        return 0.0
    return sum(passage in relevant for passage in shown[:k]) / len(relevant)


def reciprocal_rank(shown: list[str | None], relevant: set[str], k: int) -> float:
    """1 over the rank of the first relevant passage among the first k shown, or 0 if none
    is."""
    for rank, passage in enumerate(shown[:k], start=1):
        if passage in relevant:
            return 1 / rank
    return 0.0


def ndcg(shown: list[str | None], relevant: set[str], k: int) -> float:
    """The DCG of the first k shown over that of the best ranking there is, the relevant
    passages first, or 0 if no passage is relevant."""
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, passage in enumerate(shown[:k], start=1)
        if passage in relevant
    )
    best = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return dcg / best if best else 0.0


def mean(
    measure: Measure,
    run: dict[str, list[str | None]],
    judgments: dict[str, set[str]],
    k: int,
) -> float:
    """The measure's mean over every question judged, a question the run shows nothing for
    scoring 0."""
    total = sum(
        measure(run.get(question, []), relevant, k)
        for question, relevant in judgments.items()
    )
    return total / len(judgments)
