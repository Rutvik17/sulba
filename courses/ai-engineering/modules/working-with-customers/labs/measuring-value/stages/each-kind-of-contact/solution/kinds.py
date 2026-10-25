"""The desk's agent on each kind of contact: the share of each task's trials it did, averaged
over the kind's tasks, with the standard error of that average."""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Share:
    """A kind's share of trials done: the mean over its tasks of each task's share, the
    standard error of that mean, and how many tasks it has."""

    value: float
    error: float
    tasks: int


def by_kind(runs: list[dict[str, str]], variant: str) -> dict[str, Share]:
    """Each kind's share for the variant, from runs.csv's rows, in the order the kinds first
    appear."""
    trials: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for run in runs:
        if run["variant"] == variant:
            trials[run["kind"]][run["task"]].append(run["outcome"] == "done")
    shares = {}
    for kind, tasks in trials.items():
        if len(tasks) < 2:
            raise ValueError(f"{kind} has one task, which can't show a spread")
        each = [sum(done) / len(done) for done in tasks.values()]
        error = statistics.stdev(each) / math.sqrt(len(each))
        shares[kind] = Share(statistics.fmean(each), error, len(each))
    return shares
