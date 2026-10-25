"""An agent's success over repeated trials of each task: pass@k, the chance that at least one of
k trials does the task, and pass^k, the chance that all k do, each averaged over the tasks with
an interval that counts each task once."""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from statistics import NormalDist


def pass_at_k(n: int, c: int, k: int) -> float:
    """The chance that at least one of k of a task's n trials, c of which did the task, did it:
    1 - C(n - c, k) / C(n, k)."""
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """The chance that all k of a task's n trials, c of which did the task, did it:
    C(c, k) / C(n, k)."""
    raise NotImplementedError


def trials(runs: list[dict[str, str]], variant: str) -> dict[str, tuple[int, int]]:
    """Each task's trials by the variant and how many of them did the task, from runs.csv's
    rows."""
    raise NotImplementedError


@dataclass(frozen=True)
class Score:
    """A score averaged over tasks, with its interval: the mean of each task's score, plus or
    minus z standard errors of that mean, z for the confidence."""

    value: float
    low: float
    high: float


def score(
    counts: dict[str, tuple[int, int]],
    k: int,
    every: bool = True,
    confidence: float = 0.95,
) -> Score:
    """pass^k over the tasks, or pass@k when every is False, with its interval."""
    raise NotImplementedError
