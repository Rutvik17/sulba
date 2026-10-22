"""The desk's recorded long conversations held by the last lab's agent and by this stage's, with
a memory: how many runs the server refused a request of, how large requests grew, the share of
each kind of part done, this stage's less the last's, conversation by conversation, with its
95% interval, what the memory did, and what it cost in time and in the server's cache."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

CONFIDENCE = 0.95
KINDS = ["question", "callback", "all"]


def signed(value: float) -> str:
    """value to three places, with its sign, or 0.000 when it rounds to nothing."""
    shown = f"{value:+.3f}"
    return "0.000" if shown[1:] == "0.000" else shown


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        parts = list(csv.DictReader(file))
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    out = {"confidence": f"{CONFIDENCE:.0%}"}
    done: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for part in parts:
        for kind in (part["kind"], "all"):
            done[part["variant"], kind][part["conversation"]].append(
                float(part["outcome"] == "done")
            )
    conversations = sorted({part["conversation"] for part in parts})
    for kind in KINDS:
        shares = {
            variant: [
                statistics.mean(done[variant, kind][each]) for each in conversations
            ]
            for variant in ("whole", "memory")
        }
        differences = [m - w for m, w in zip(shares["memory"], shares["whole"])]
        mean = statistics.mean(differences)
        margin = z * statistics.stdev(differences) / math.sqrt(len(differences))
        out[f"{kind}_whole"] = f"{statistics.mean(shares['whole']):.3f}"
        out[f"{kind}_memory"] = f"{statistics.mean(shares['memory']):.3f}"
        out[f"{kind}_difference"] = signed(mean)
        out[f"{kind}_interval"] = f"{signed(mean - margin)} to {signed(mean + margin)}"
    for variant in ("whole", "memory"):
        mine = [part for part in parts if part["variant"] == variant]
        runs: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for part in mine:
            runs[part["conversation"], part["trial"]].append(part)
        reached = [part for part in mine if part["outcome"] != "error"]
        largest = [
            max(int(part["largest_prompt"]) for part in run) for run in runs.values()
        ]
        prompt = sum(int(part["prompt_tokens"]) for part in reached)
        cached = sum(int(part["cached_tokens"]) for part in reached)
        refused = sum(
            any(part["refused"] == "context" for part in run) for run in runs.values()
        )
        out[f"{variant}_refused"] = f"{refused}"
        out[f"{variant}_largest"] = f"{statistics.median(largest):,.0f}"
        out[f"{variant}_most"] = f"{max(largest):,}"
        out[f"{variant}_seconds"] = (
            f"{statistics.mean(float(part['seconds']) for part in reached):.0f}"
        )
        out[f"{variant}_cached"] = f"{cached / prompt:.0%}"
    memory = [part for part in parts if part["variant"] == "memory"]
    out["cleared"] = f"{sum(int(part['cleared']) for part in memory)}"
    out["summaries"] = f"{sum(int(part['summaries']) for part in memory)}"
    return out
