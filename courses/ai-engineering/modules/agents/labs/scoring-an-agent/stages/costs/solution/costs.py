"""What an agent's runs cost: each task's seconds and tokens, and their percentiles over the
tasks, each with an interval from the order statistics, which assumes nothing about how the
costs are spread."""

import math
import statistics
from collections import defaultdict


def cost(run: dict[str, str], measure: str) -> float:
    """A run's seconds, or its tokens: those of its prompts and of its replies."""
    if measure == "seconds":
        return float(run["seconds"])
    if measure == "tokens":
        return float(int(run["prompt_tokens"]) + int(run["completion_tokens"]))
    raise ValueError(f'measure is "seconds" or "tokens", not {measure!r}.')


def per_task(
    runs: list[dict[str, str]], variant: str, measure: str
) -> dict[str, float]:
    """Each task's median, over the variant's trials of it, of the measure."""
    costs: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        if run["variant"] == variant:
            costs[run["task"]].append(cost(run, measure))
    return {task: statistics.median(each) for task, each in costs.items()}


def quantile(values: list[float], p: float) -> float:
    """The p-quantile of the values, as NumPy's quantile gives it by default: at the position
    (n - 1)p in the values sorted, between the two values on either side, in proportion."""
    ordered = sorted(values)
    at = (len(ordered) - 1) * p
    below = math.floor(at)
    above = min(below + 1, len(ordered) - 1)
    return ordered[below] + (at - below) * (ordered[above] - ordered[below])


def binomial_cdf(k: int, n: int, p: float) -> float:
    """The chance of at most k successes in n trials, each a success with the chance p."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def interval(
    values: list[float], p: float, confidence: float = 0.95
) -> tuple[float, float]:
    """The interval for the p-quantile of what the values were drawn from, as SciPy's
    quantile_test gives it: with a = (1 - confidence) / 2, from the jth smallest value, j the
    least count of values below the quantile whose chance is at least a, to the value after the
    kth, k the least count whose chance of being passed is at most a; nan for an end there
    aren't enough values for."""
    ordered = sorted(values)
    n = len(ordered)
    a = (1 - confidence) / 2
    low_at = next(k for k in range(n + 1) if binomial_cdf(k, n, p) >= a) - 1
    high_at = next(k for k in range(n + 1) if 1 - binomial_cdf(k, n, p) <= a)
    low = ordered[low_at] if low_at >= 0 else math.nan
    high = ordered[high_at] if high_at < n else math.nan
    return low, high
