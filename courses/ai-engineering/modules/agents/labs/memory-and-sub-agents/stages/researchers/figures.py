"""The desk's recorded long conversations held by the last stage's agent, with a memory, and by
this stage's, with researchers: how large the agent's requests grew, the tokens of prompt its
requests and the researchers' sent, the share of each kind of part done, this stage's less the
last's, conversation by conversation, with its 95% interval, the questions answered from the
wrong passage, what the memory did, the time each part took and the server's cache."""

import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

CONFIDENCE = 0.95
KINDS = ["question", "callback", "all"]
VARIANTS = ["memory", "researchers"]


def signed(value: float) -> str:
    """value to three places, with its sign, or 0.000 when it rounds to nothing."""
    shown = f"{value:+.3f}"
    return "0.000" if shown[1:] == "0.000" else shown


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        parts = [part for part in csv.DictReader(file) if part["variant"] in VARIANTS]
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
            for variant in VARIANTS
        }
        differences = [r - m for r, m in zip(shares["researchers"], shares["memory"])]
        mean = statistics.mean(differences)
        margin = z * statistics.stdev(differences) / math.sqrt(len(differences))
        out[f"{kind}_memory"] = f"{statistics.mean(shares['memory']):.3f}"
        out[f"{kind}_researchers"] = f"{statistics.mean(shares['researchers']):.3f}"
        out[f"{kind}_difference"] = signed(mean)
        out[f"{kind}_interval"] = f"{signed(mean - margin)} to {signed(mean + margin)}"
    for variant in VARIANTS:
        mine = [part for part in parts if part["variant"] == variant]
        runs: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for part in mine:
            runs[part["conversation"], part["trial"]].append(part)
        reached = [part for part in mine if part["outcome"] != "error"]
        largest = [
            max(int(part["largest_prompt"]) for part in run) for run in runs.values()
        ]
        agent = [
            sum(int(part["prompt_tokens"]) for part in run) for run in runs.values()
        ]
        out[f"{variant}_largest"] = f"{statistics.median(largest):,.0f}"
        out[f"{variant}_agent"] = f"{statistics.median(agent):,.0f}"
        out[f"{variant}_seconds"] = (
            f"{statistics.mean(float(part['seconds']) for part in reached):.0f}"
        )
        prompt = sum(int(part["prompt_tokens"]) for part in reached)
        cached = sum(int(part["cached_tokens"]) for part in reached)
        out[f"{variant}_cached"] = f"{cached / prompt:.0%}"
        questions = [part for part in mine if part["kind"] == "question"]
        miscited = sum(
            part["outcome"] == "cited no passage with the answer" for part in questions
        )
        out[f"{variant}_miscited"] = f"{miscited / len(questions):.3f}"
        out[f"{variant}_compacted"] = (
            f"{sum(int(part['cleared']) + int(part['summaries']) for part in mine)}"
        )
        if variant == "researchers":
            researched = [
                sum(int(part["researcher_prompt_tokens"]) for part in run)
                for run in runs.values()
            ]
            out["researched"] = f"{statistics.median(researched):,.0f}"
    return out
