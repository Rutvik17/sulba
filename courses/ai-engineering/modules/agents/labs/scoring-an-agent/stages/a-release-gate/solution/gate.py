"""The desk's release gate: whether a candidate agent may replace the current one, from both
agents' trials of the same tasks."""

import math
import statistics
from dataclasses import dataclass
from statistics import NormalDist

from costs import interval, per_task, quantile
from scores import Score, pass_hat_k, trials


@dataclass(frozen=True)
class Verdict:
    """The candidate's pass^k less the current agent's, over the tasks; the candidate's 90th
    percentile of seconds; and what it was held for, if anything."""

    difference: Score
    tail: Score
    held: tuple[str, ...]

    @property
    def ship(self) -> bool:
        return not self.held


def gate(
    runs: list[dict[str, str]],
    current: str,
    candidate: str,
    *,
    k: int,
    tolerance: float,
    seconds: float,
    confidence: float = 0.95,
) -> Verdict:
    """The verdict on the candidate: held for its pass^k when it may be lower than the current
    agent's by more than tolerance, and for its seconds when its 90th percentile may be over
    seconds."""
    before, after = trials(runs, current), trials(runs, candidate)
    if before.keys() != after.keys():
        raise ValueError(f"{current} and {candidate} ran different tasks.")
    if any(before[task][0] != after[task][0] for task in before):
        raise ValueError(
            f"{current} and {candidate} ran some task a different number of times."
        )
    if any(n < k for n, _ in before.values()):
        raise ValueError(f"pass^{k} needs at least {k} trials of each task.")
    differences = [
        pass_hat_k(*after[task], k) - pass_hat_k(*before[task], k) for task in before
    ]
    mean = statistics.mean(differences)
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    margin = z * statistics.stdev(differences) / math.sqrt(len(differences))
    difference = Score(mean, mean - margin, mean + margin)
    medians = list(per_task(runs, candidate, "seconds").values())
    tail = Score(quantile(medians, 0.9), *interval(medians, 0.9, confidence))
    held = []
    if difference.low < -tolerance:
        held.append("pass^k")
    # An interval with no high end can't show the percentile is within the budget.
    if not tail.high <= seconds:
        held.append("seconds")
    return Verdict(difference, tail, tuple(held))
