"""What each of the scorecard's problems would have changed on the Tools and planning lab's runs
of its two agents: pass^5 estimated as (c/n)^5; the margin of pass^5's interval at 95% and at
the 90% that z for a one-sided 95% gives; the 90th percentile's interval in seconds over every
run and over each task's median; and the tasks, and the failed runs, that costs taken from the
runs that were done leave out."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

VARIANTS = {"last": "agent", "this": "proposals"}
K = 5


def interval(values: list[float], p: float) -> tuple[float, float]:
    ordered = sorted(values)
    n = len(ordered)
    a = 0.025
    cdf = [0.0]
    for k in range(n + 1):
        cdf.append(cdf[-1] + math.comb(n, k) * p**k * (1 - p) ** (n - k))
    low = next(k for k in range(n + 1) if cdf[k + 1] >= a) - 1
    high = next(k for k in range(n + 1) if 1 - cdf[k + 1] <= a)
    assert 0 <= low and high < n
    return ordered[low], ordered[high]


def quantile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    at = (len(ordered) - 1) * p
    below = math.floor(at)
    above = min(below + 1, len(ordered) - 1)
    return ordered[below] + (at - below) * (ordered[above] - ordered[below])


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = list(csv.DictReader(file))
    out = {"k": f"{K}"}
    for name, variant in VARIANTS.items():
        mine = [run for run in runs if run["variant"] == variant]
        done: dict[str, list[bool]] = defaultdict(list)
        seconds: dict[str, list[float]] = defaultdict(list)
        for run in mine:
            done[run["task"]].append(run["outcome"] == "done")
            seconds[run["task"]].append(float(run["seconds"]))
        out["tasks"] = f"{len(done)}"
        unbiased = [
            math.comb(sum(each), K) / math.comb(len(each), K) for each in done.values()
        ]
        plugged = [(sum(each) / len(each)) ** K for each in done.values()]
        out[f"{name}_every"] = f"{statistics.mean(unbiased):.3f}"
        out[f"{name}_plugged"] = f"{statistics.mean(plugged):.3f}"
        error = statistics.stdev(unbiased) / math.sqrt(len(unbiased))
        out[f"{name}_margin_95"] = f"{NormalDist().inv_cdf(0.975) * error:.3f}"
        out[f"{name}_margin_90"] = f"{NormalDist().inv_cdf(0.95) * error:.3f}"
        for k in (1, K):
            values = [
                math.comb(sum(each), k) / math.comb(len(each), k)
                for each in done.values()
            ]
            mean = statistics.mean(values)
            margin = (
                NormalDist().inv_cdf(0.975)
                * statistics.stdev(values)
                / math.sqrt(len(values))
            )
            out[f"{name}_card_every_{k}"] = (
                f"{mean:.3f}, from {mean - margin:.3f} to {mean + margin:.3f}"
            )
        for measure in ("seconds", "tokens"):
            costs: dict[str, list[float]] = defaultdict(list)
            for run in mine:
                costs[run["task"]].append(
                    float(run["seconds"])
                    if measure == "seconds"
                    else float(
                        int(run["prompt_tokens"]) + int(run["completion_tokens"])
                    )
                )
            each_median = [statistics.median(each) for each in costs.values()]
            shown = "{:.1f}" if measure == "seconds" else "{:,.0f}"
            for percentile, p in (("median", 0.5), ("p90", 0.9)):
                ends = interval(each_median, p)
                out[f"{name}_card_{percentile}_{measure}"] = (
                    f"{shown.format(quantile(each_median, p))}, from "
                    f"{shown.format(ends[0])} to {shown.format(ends[1])}"
                )
        medians = [statistics.median(each) for each in seconds.values()]
        pooled = [value for each in seconds.values() for value in each]
        for kind, values in (("tasks", medians), ("pooled", pooled)):
            low, high = interval(values, 0.9)
            out[f"{name}_{kind}_p90_low"], out[f"{name}_{kind}_p90_high"] = (
                f"{low:.1f}",
                f"{high:.1f}",
            )
        out[f"{name}_never"] = f"{sum(not any(each) for each in done.values())}"
        failed = [float(run["seconds"]) for run in mine if run["outcome"] != "done"]
        succeeded = [float(run["seconds"]) for run in mine if run["outcome"] == "done"]
        out[f"{name}_failed_runs"] = f"{len(failed)}"
        out[f"{name}_failed_median"] = f"{statistics.median(failed):.1f}"
        out[f"{name}_done_median"] = f"{statistics.median(succeeded):.1f}"
    return out
