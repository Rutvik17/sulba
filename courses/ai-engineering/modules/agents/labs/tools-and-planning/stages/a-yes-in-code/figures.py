"""The agent's recorded runs of the desk's tasks on the last lab's tools and on this lab's
compared: the share of runs each did, by kind of task, this lab's share less the last's, task by
task, with its 95% interval, why runs fell short, and what a run took."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

KINDS = ["question", "case", "callback", "new", "vague"]
CONFIDENCE = 0.95
VARIANTS = {"last": "agent", "this": "proposals"}
UNMADE = {"opened 0 tickets", "booked 0 callbacks"}


def signed(value: float) -> str:
    """value to three places, with its sign, or 0.000 when it rounds to nothing."""
    shown = f"{value:+.3f}"
    return "0.000" if shown[1:] == "0.000" else shown


def first_turn(calls: str) -> list[str]:
    """The tools the model called before its first reply, from a run's calls: a turn's requests
    end with the first that called none."""
    called = []
    for request in calls.split("|"):
        if not request:
            break
        called += request.split()
    return called


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = list(csv.DictReader(file))
    done: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    kinds = {}
    for run in runs:
        done[run["variant"]][run["task"]].append(float(run["outcome"] == "done"))
        kinds[run["task"]] = run["kind"]
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    out = {
        "tasks": f"{len(kinds)}",
        "trials": f"{len(next(iter(done['proposals'].values())))}",
        "confidence": f"{CONFIDENCE:.0%}",
    }
    for kind in [*KINDS, "all"]:
        tasks = [task for task in kinds if kind in ("all", kinds[task])]
        shares = {
            name: [statistics.mean(done[variant][task]) for task in tasks]
            for name, variant in VARIANTS.items()
        }
        differences = [t - s for t, s in zip(shares["this"], shares["last"])]
        mean = statistics.mean(differences)
        margin = z * statistics.stdev(differences) / math.sqrt(len(tasks))
        out[f"{kind}_last"] = f"{statistics.mean(shares['last']):.3f}"
        out[f"{kind}_this"] = f"{statistics.mean(shares['this']):.3f}"
        out[f"{kind}_difference"] = signed(mean)
        out[f"{kind}_interval"] = f"{signed(mean - margin)} to {signed(mean + margin)}"
    for name, variant in VARIANTS.items():
        mine = [run for run in runs if run["variant"] == variant]
        questions = [run for run in mine if run["kind"] == "question"]
        acts = [run for run in mine if run["kind"] in ("case", "callback", "new")]
        uncited = sum(run["outcome"] == "cited no passage" for run in questions)
        miscited = sum(
            run["outcome"] == "cited no passage with the answer" for run in questions
        )
        early = sum(run["outcome"] == "wrote before the caller's yes" for run in acts)
        unmade = sum(run["outcome"] in UNMADE for run in acts)
        out[f"{name}_uncited"] = f"{uncited / len(questions):.3f}"
        out[f"{name}_miscited"] = f"{miscited / len(questions):.3f}"
        out[f"{name}_early"] = f"{early / len(acts):.3f}"
        out[f"{name}_unmade"] = f"{unmade / len(acts):.3f}"
        seconds = statistics.median(float(run["seconds"]) for run in mine)
        requests = statistics.mean(int(run["requests"]) for run in mine)
        tokens = statistics.mean(int(run["prompt_tokens"]) for run in mine)
        out[f"{name}_seconds"] = f"{seconds:.0f}"
        out[f"{name}_requests"] = f"{requests:.1f}"
        out[f"{name}_tokens"] = f"{tokens:,.0f}"
    unmade = [
        (run["kind"], first_turn(run["calls"]))
        for run in runs
        if run["variant"] == "proposals" and run["outcome"] in UNMADE
    ]
    proposed = [
        (kind, {tool for tool in called if tool.startswith("propose_")})
        for kind, called in unmade
    ]
    out["unmade"] = f"{len(unmade)}"
    out["unmade_asked"] = f"{sum(not tools for _, tools in proposed)}"
    out["unmade_ticket"] = (
        f"{sum(kind == 'new' and tools == {'propose_ticket'} for kind, tools in proposed)}"
    )
    return out
