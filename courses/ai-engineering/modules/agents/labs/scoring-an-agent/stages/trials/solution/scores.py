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
    if not 0 < k <= n or not 0 <= c <= n:
        raise ValueError(
            f"k is from 1 to n = {n}, and c from 0 to n; they're {k} and {c}."
        )
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """The chance that all k of a task's n trials, c of which did the task, did it:
    C(c, k) / C(n, k)."""
    if not 0 < k <= n or not 0 <= c <= n:
        raise ValueError(
            f"k is from 1 to n = {n}, and c from 0 to n; they're {k} and {c}."
        )
    return math.comb(c, k) / math.comb(n, k)


def trials(runs: list[dict[str, str]], variant: str) -> dict[str, tuple[int, int]]:
    """Each task's trials by the variant and how many of them did the task, from runs.csv's
    rows."""
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for run in runs:
        if run["variant"] == variant:
            counts[run["task"]][0] += 1
            counts[run["task"]][1] += run["outcome"] == "done"
    return {task: (n, c) for task, (n, c) in counts.items()}


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
    estimate = pass_hat_k if every else pass_at_k
    values = [estimate(n, c, k) for n, c in counts.values()]
    mean = statistics.mean(values)
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    margin = z * statistics.stdev(values) / math.sqrt(len(values))
    return Score(mean, mean - margin, mean + margin)
