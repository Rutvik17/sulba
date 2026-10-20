"""The help desk's release check: whether a new search may replace the current one."""

from dataclasses import dataclass

import numpy as np

K = 5
DEPTH = 10
REPEATS = 10_000
LEVEL = 0.05
# The most a service's hit rate may fall.
FALL = 0.03


@dataclass
class Release:
    """What a release check found: each search's hit rate at K and nDCG at DEPTH over every
    question, the current search's first; the p-value of the difference in hit rate; each
    service's two hit rates; the services whose hit rate falls by more than FALL; and
    whether the candidate ships."""

    hit_rate: tuple[float, float]
    ndcg: tuple[float, float]
    p: float
    services: dict[str, tuple[float, float]]
    held: list[str]
    ship: bool


def check(
    current: dict[str, list[str]],
    candidate: dict[str, list[str]],
    judgments: dict[str, set[str]],
    first: dict[str, str],
    services: dict[str, str],
    rng: np.random.Generator,
) -> Release:
    """Whether the candidate search may replace the current one, by their passages for the
    questions judged, as a reader sees them."""
    raise NotImplementedError
