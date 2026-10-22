"""The desk's recorded long conversations held by the last lab's agent, which sends the whole
conversation in each request: how many runs the server refused a request of for its size, at
which part, and how large the runs' requests grew."""

import csv
import statistics
from collections import defaultdict


def figures() -> dict[str, str]:
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        parts = [part for part in csv.DictReader(file) if part["variant"] == "whole"]
    runs: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for part in parts:
        runs[part["conversation"], part["trial"]].append(part)
    refused = [
        min(int(part["part"]) for part in run if part["refused"] == "context")
        for run in runs.values()
        if any(part["refused"] == "context" for part in run)
    ]
    largest = [
        max(int(part["largest_prompt"]) for part in run) for run in runs.values()
    ]
    first = next(iter(runs.values()))
    return {
        "conversations": f"{len({part['conversation'] for part in parts})}",
        "trials": f"{len({part['trial'] for part in parts})}",
        "runs": f"{len(runs)}",
        "parts": f"{len(first)}",
        "questions": f"{sum(part['kind'] == 'question' for part in first)}",
        "refused": f"{len(refused)}",
        "refused_part": f"{statistics.median(refused):.0f}",
        "largest": f"{statistics.median(largest):,.0f}",
    }
