import csv
import math
import statistics
from collections import Counter, defaultdict

KINDS = ["question", "case", "callback", "new", "vague"]


def figures():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = [row for row in csv.DictReader(file) if row["variant"] == "agent"]
    tasks = defaultdict(lambda: defaultdict(list))
    for run in runs:
        tasks[run["kind"]][run["task"]].append(run["outcome"] == "done")
    out = {"trials": f"{len(runs):,}", "tasks": f"{sum(map(len, tasks.values()))}"}
    for kind in KINDS:
        each = [sum(done) / len(done) for done in tasks[kind].values()]
        out[f"{kind}_tasks"] = f"{len(each)}"
        out[f"{kind}_done"] = f"{statistics.fmean(each):.1%}"
        error = statistics.stdev(each) / math.sqrt(len(each))
        out[f"{kind}_error"] = f"{error * 100:.1f}"
    outcomes = Counter(run["outcome"] for run in runs)
    early = outcomes["wrote before the caller's yes"]
    out["early"] = f"{early}"
    out["pooled"] = f"{outcomes['done'] / len(runs):.1%}"
    return out
