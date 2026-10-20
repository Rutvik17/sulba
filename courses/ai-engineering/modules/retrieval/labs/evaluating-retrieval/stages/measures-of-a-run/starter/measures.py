"""Measures of the passages a search shows for one question, and their mean over a run."""

from collections.abc import Callable

Measure = Callable[[list[str | None], set[str], int], float]


def hit_rate(shown: list[str | None], relevant: set[str], k: int) -> float:
    """1 if a relevant passage is among the first k shown, else 0."""
    raise NotImplementedError


def recall(shown: list[str | None], relevant: set[str], k: int) -> float:
    """The share of the relevant passages that are among the first k shown, or 0 if no
    passage is relevant."""
    raise NotImplementedError


def reciprocal_rank(shown: list[str | None], relevant: set[str], k: int) -> float:
    """1 over the rank of the first relevant passage among the first k shown, or 0 if none
    is."""
    raise NotImplementedError


def ndcg(shown: list[str | None], relevant: set[str], k: int) -> float:
    """The DCG of the first k shown over that of the best ranking there is, the relevant
    passages first, or 0 if no passage is relevant."""
    raise NotImplementedError


def mean(
    measure: Measure,
    run: dict[str, list[str | None]],
    judgments: dict[str, set[str]],
    k: int,
) -> float:
    """The measure's mean over every question judged, a question the run shows nothing for
    scoring 0."""
    raise NotImplementedError
