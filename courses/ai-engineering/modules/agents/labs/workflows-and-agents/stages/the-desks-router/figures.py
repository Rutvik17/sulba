"""The router's recorded runs of the desk's tasks beside the workflow's and the agent's: the
share each did, by kind of task, the router's share less each of the others', task by task,
with its 95% interval, the runs it sent the agent, its runs down the workflow's paths that came
out otherwise than the workflow's own, and what a run took."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

KINDS = ["question", "case", "callback", "new", "vague"]
VARIANTS = ["workflow", "agent", "router"]
CONFIDENCE = 0.95


def signed(value: float) -> str:
    """value to three places, with its sign, or 0.000 when it rounds to nothing."""
    shown = f"{value:+.3f}"
    return "0.000" if shown[1:] == "0.000" else shown


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = list(csv.DictReader(file))
    done: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    kinds = {}
    for run in runs:
        done[run["variant"]][run["task"]].append(float(run["outcome"] == "done"))
        kinds[run["task"]] = run["kind"]
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    out = {"confidence": f"{CONFIDENCE:.0%}"}
    for kind in [*KINDS, "all"]:
        tasks = [task for task in kinds if kind in ("all", kinds[task])]
        shares = {
            variant: [statistics.mean(done[variant][task]) for task in tasks]
            for variant in VARIANTS
        }
        for variant in VARIANTS:
            out[f"{kind}_{variant}"] = f"{statistics.mean(shares[variant]):.3f}"
    tasks = list(kinds)
    for other in ("workflow", "agent"):
        differences = [
            statistics.mean(done["router"][task]) - statistics.mean(done[other][task])
            for task in tasks
        ]
        mean = statistics.mean(differences)
        margin = z * statistics.stdev(differences) / math.sqrt(len(tasks))
        out[f"less_{other}"] = signed(mean)
        out[f"less_{other}_interval"] = (
            f"{signed(mean - margin)} to {signed(mean + margin)}"
        )
    router = [run for run in runs if run["variant"] == "router"]
    agent = [run for run in router if run["path"] == "agent"]
    out["router_runs"] = f"{len(router)}"
    out["to_agent"] = f"{len(agent)}"
    out["to_agent_vague"] = f"{sum(run['kind'] == 'vague' for run in agent)}"
    workflow = {
        (run["task"], run["trial"]): run["outcome"]
        for run in runs
        if run["variant"] == "workflow"
    }
    followed = [run for run in router if run["path"] == "workflow"]
    otherwise = [
        run for run in followed if run["outcome"] != workflow[run["task"], run["trial"]]
    ]
    out["on_path"] = f"{len(followed)}"
    out["otherwise"] = f"{len(otherwise)}"
    for variant in VARIANTS:
        mine = [run for run in runs if run["variant"] == variant]
        seconds = statistics.median(float(run["seconds"]) for run in mine)
        out[f"{variant}_seconds"] = f"{seconds:.0f}"
    return out
