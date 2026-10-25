"""The seconds and tokens of the Tools and planning lab's two agents on the desk's 120 tasks:
each task's median over its five trials, and the median and 90th percentile of those over the
tasks, each with its 95% interval from the order statistics; and the 90th percentile of every
run's seconds, as if each run were a task of its own."""

import csv
import json
import math
import statistics
from collections import defaultdict

VARIANTS = {"last": "agent", "this": "proposals"}
CONFIDENCE = 0.95
PERCENTILES = {"median": 0.5, "p90": 0.9}


def quantile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    at = (len(ordered) - 1) * p
    below = math.floor(at)
    above = min(below + 1, len(ordered) - 1)
    return ordered[below] + (at - below) * (ordered[above] - ordered[below])


def interval(values: list[float], p: float) -> tuple[float, float]:
    ordered = sorted(values)
    n = len(ordered)
    a = (1 - CONFIDENCE) / 2
    cdf = [0.0]
    for k in range(n + 1):
        cdf.append(cdf[-1] + math.comb(n, k) * p**k * (1 - p) ** (n - k))
    low = next(k for k in range(n + 1) if cdf[k + 1] >= a) - 1
    high = next(k for k in range(n + 1) if 1 - cdf[k + 1] <= a)
    assert 0 <= low and high < n
    return ordered[low], ordered[high]


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = list(csv.DictReader(file))
    shown = {"seconds": "{:.1f}", "tokens": "{:,.0f}"}
    cases = json.loads(open("references/quantiles.json", encoding="utf-8").read())[
        "cases"
    ]
    out = {"confidence": f"{CONFIDENCE:.0%}", "cases": f"{len(cases)}"}
    for name, variant in VARIANTS.items():
        costs: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for run in runs:
            if run["variant"] == variant:
                costs["seconds"][run["task"]].append(float(run["seconds"]))
                costs["tokens"][run["task"]].append(
                    float(int(run["prompt_tokens"]) + int(run["completion_tokens"]))
                )
        out["tasks"] = f"{len(costs['seconds'])}"
        out["runs"] = f"{sum(map(len, costs['seconds'].values()))}"
        out["trials"] = f"{len(next(iter(costs['seconds'].values())))}"
        for measure, tasks in costs.items():
            medians = [statistics.median(each) for each in tasks.values()]
            for percentile, p in PERCENTILES.items():
                key = f"{name}_{measure}_{percentile}"
                out[key] = shown[measure].format(quantile(medians, p))
                ends = interval(medians, p)
                out[f"{key}_low"], out[f"{key}_high"] = (
                    shown[measure].format(end) for end in ends
                )
            if measure == "seconds":
                out["past_p90"] = f"{sum(m > quantile(medians, 0.9) for m in medians)}"
        pooled = [seconds for each in costs["seconds"].values() for seconds in each]
        low, high = interval(pooled, 0.9)
        out[f"{name}_pooled_p90"] = f"{quantile(pooled, 0.9):.1f}"
        out[f"{name}_pooled_p90_low"], out[f"{name}_pooled_p90_high"] = (
            f"{low:.1f}",
            f"{high:.1f}",
        )
        slowest = max(
            costs["seconds"], key=lambda task: statistics.median(costs["seconds"][task])
        )
        if name == "this":
            median = statistics.median(costs["seconds"][slowest])
            out["this_slowest_median"] = f"{median:.1f}"
        out[f"{name}_slowest_runs"] = ", ".join(
            f"{seconds:.1f}" for seconds in sorted(costs["seconds"][slowest])
        )
    return out
