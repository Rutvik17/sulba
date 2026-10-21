"""The workflow's and the agent's recorded runs of the desk's tasks compared: the share of runs
each did, by kind of task, the agent's share less the workflow's, task by task, with its 95%
interval, why the agent's runs fell short, and what a run took."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

KINDS = ["question", "case", "callback", "new", "vague"]
CONFIDENCE = 0.95


def signed(value: float) -> str:
    """value to three places, with its sign, or 0.000 when it rounds to nothing."""
    shown = f"{value:+.3f}"
    return "0.000" if shown[1:] == "0.000" else shown


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = [run for run in csv.DictReader(file) if run["variant"] != "router"]
    done: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    kinds = {}
    for run in runs:
        done[run["variant"]][run["task"]].append(float(run["outcome"] == "done"))
        kinds[run["task"]] = run["kind"]
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    out = {
        "tasks": f"{len(kinds)}",
        "confidence": f"{CONFIDENCE:.0%}",
        "workflow_trials": f"{len(next(iter(done['workflow'].values())))}",
        "agent_trials": f"{len(next(iter(done['agent'].values())))}",
    }
    for kind in [*KINDS, "all"]:
        tasks = [task for task in kinds if kind in ("all", kinds[task])]
        shares = {
            variant: [statistics.mean(done[variant][task]) for task in tasks]
            for variant in ("workflow", "agent")
        }
        differences = [a - w for a, w in zip(shares["agent"], shares["workflow"])]
        mean = statistics.mean(differences)
        margin = z * statistics.stdev(differences) / math.sqrt(len(tasks))
        out[f"{kind}_workflow"] = f"{statistics.mean(shares['workflow']):.3f}"
        out[f"{kind}_agent"] = f"{statistics.mean(shares['agent']):.3f}"
        out[f"{kind}_difference"] = signed(mean)
        out[f"{kind}_interval"] = f"{signed(mean - margin)} to {signed(mean + margin)}"
    agent = [run for run in runs if run["variant"] == "agent"]
    questions = [run for run in agent if run["kind"] == "question"]
    acts = [run for run in agent if run["kind"] in ("case", "callback", "new")]
    uncited = sum(run["outcome"] == "cited no passage" for run in questions)
    early = sum(run["outcome"] == "wrote before the caller's yes" for run in acts)
    out["uncited"] = f"{uncited / len(questions):.3f}"
    out["early"] = f"{early / len(acts):.3f}"
    for variant in ("workflow", "agent"):
        mine = [run for run in runs if run["variant"] == variant]
        seconds = statistics.median(float(run["seconds"]) for run in mine)
        requests = statistics.mean(int(run["requests"]) for run in mine)
        tokens = statistics.mean(int(run["prompt_tokens"]) for run in mine)
        out[f"{variant}_seconds"] = f"{seconds:.0f}"
        out[f"{variant}_requests"] = f"{requests:.1f}"
        out[f"{variant}_tokens"] = f"{tokens:,.0f}"
    return out
