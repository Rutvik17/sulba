"""The release gate on the Tools and planning lab's two agents, each in turn the candidate to
replace the other, at k = 5, a tolerance of 0.05 and a budget of 180 seconds: the candidate's
pass^5 less the current agent's, task by task, with its 95% interval, and the candidate's 90th
percentile of seconds over each task's median, with its interval from the order statistics."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

VARIANTS = {"first": "agent", "new": "proposals"}
K = 5
TOLERANCE = 0.05
BUDGET = 180
CONFIDENCE = 0.95


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
    done: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    seconds: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for run in runs:
        done[run["variant"]][run["task"]].append(run["outcome"] == "done")
        seconds[run["variant"]][run["task"]].append(float(run["seconds"]))
    out = {
        "k": f"{K}",
        "tolerance": f"{TOLERANCE:.2f}",
        "budget": f"{BUDGET}",
        "confidence": f"{CONFIDENCE:.0%}",
        "tasks": f"{len(done['agent'])}",
    }
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    for candidate, current in (("new", "first"), ("first", "new")):
        after, before = done[VARIANTS[candidate]], done[VARIANTS[current]]
        assert after.keys() == before.keys()
        differences = [
            math.comb(sum(after[task]), K) / math.comb(len(after[task]), K)
            - math.comb(sum(before[task]), K) / math.comb(len(before[task]), K)
            for task in before
        ]
        mean = statistics.mean(differences)
        margin = z * statistics.stdev(differences) / math.sqrt(len(differences))
        out[f"{candidate}_difference"] = f"{mean:+.3f}"
        out[f"{candidate}_difference_low"] = f"{mean - margin:+.3f}"
        out[f"{candidate}_difference_high"] = f"{mean + margin:+.3f}"
        medians = [
            statistics.median(each) for each in seconds[VARIANTS[candidate]].values()
        ]
        low, high = interval(medians, 0.9)
        out[f"{candidate}_tail"] = f"{quantile(medians, 0.9):.1f}"
        out[f"{candidate}_tail_low"], out[f"{candidate}_tail_high"] = (
            f"{low:.1f}",
            f"{high:.1f}",
        )
        held = []
        if mean - margin < -TOLERANCE:
            held.append("its pass^k")
        if not high <= BUDGET:
            held.append("its seconds")
        out[f"{candidate}_held"] = " and ".join(held) or "nothing"
    return out
