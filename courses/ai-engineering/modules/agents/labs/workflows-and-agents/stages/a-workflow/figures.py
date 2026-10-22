"""The workflow's recorded runs of the desk's tasks: the share done, the median seconds and the
requests of a run, by kind of task and over every task."""

import csv
import json
import statistics
from pathlib import Path

KINDS = ["question", "case", "callback", "new", "vague"]


def figures() -> dict[str, str]:
    with open(Path("data/runs.csv"), encoding="utf-8", newline="") as file:
        runs = [run for run in csv.DictReader(file) if run["variant"] == "workflow"]
    tasks = json.loads(Path("data/tasks.json").read_text(encoding="utf-8"))
    out = {
        "tasks": f"{len(tasks)}",
        "trials": f"{max(int(run['trial']) for run in runs)}",
    }
    for kind in [*KINDS, "all"]:
        mine = [run for run in runs if kind in ("all", run["kind"])]
        done = sum(run["outcome"] == "done" for run in mine) / len(mine)
        seconds = statistics.median(float(run["seconds"]) for run in mine)
        requests = statistics.mean(int(run["requests"]) for run in mine)
        out[f"{kind}_done"] = f"{done:.3f}"
        out[f"{kind}_seconds"] = f"{seconds:.1f}"
        out[f"{kind}_requests"] = f"{requests:.1f}"
    return out
