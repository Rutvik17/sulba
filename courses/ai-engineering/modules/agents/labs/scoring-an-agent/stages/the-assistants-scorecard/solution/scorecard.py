"""The desk's scorecard of its agents from runs.csv: for each agent, pass^1 and pass^k over the
tasks, and the median and 90th percentile of each task's seconds and tokens, each with its
interval."""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from statistics import NormalDist

from costs import interval, quantile

CONFIDENCE = 0.95


@dataclass(frozen=True)
class Estimate:
    """A number from the runs and its interval."""

    value: float
    low: float
    high: float


def measured(run: dict[str, str], measure: str) -> float:
    """A run's seconds, or its tokens of prompt and of reply."""
    if measure == "seconds":
        return float(run["seconds"])
    return float(int(run["prompt_tokens"]) + int(run["completion_tokens"]))


def reliability(
    runs: list[dict[str, str]], variant: str, k: int, confidence: float = CONFIDENCE
) -> Estimate:
    """pass^k over the tasks the variant ran, with its interval."""
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for run in runs:
        if run["variant"] == variant:
            counts[run["task"]][0] += 1
            counts[run["task"]][1] += run["outcome"] == "done"
    values = [math.comb(c, k) / math.comb(n, k) for n, c in counts.values()]
    mean = statistics.mean(values)
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    margin = z * statistics.stdev(values) / math.sqrt(len(values))
    return Estimate(mean, mean - margin, mean + margin)


def costs(runs: list[dict[str, str]], variant: str, measure: str) -> dict[str, float]:
    """Each task's median of the measure over the variant's runs of it."""
    by_task: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        if run["variant"] == variant:
            by_task[run["task"]].append(measured(run, measure))
    return {task: statistics.median(each) for task, each in by_task.items()}


def percentile(
    runs: list[dict[str, str]],
    variant: str,
    measure: str,
    p: float,
    confidence: float = CONFIDENCE,
) -> Estimate:
    """The p-quantile of the measure over the tasks, with its interval."""
    values = list(costs(runs, variant, measure).values())
    return Estimate(quantile(values, p), *interval(values, p, confidence))


def scorecard(
    runs: list[dict[str, str]], variants: list[str], k: int
) -> dict[str, dict[str, Estimate]]:
    """Each variant's line of the scorecard."""
    return {
        variant: {
            "pass^1": reliability(runs, variant, 1),
            f"pass^{k}": reliability(runs, variant, k),
            "median seconds": percentile(runs, variant, "seconds", 0.5),
            "p90 seconds": percentile(runs, variant, "seconds", 0.9),
            "median tokens": percentile(runs, variant, "tokens", 0.5),
            "p90 tokens": percentile(runs, variant, "tokens", 0.9),
        }
        for variant in variants
    }
