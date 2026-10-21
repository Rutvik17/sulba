# /// script
# requires-python = "==3.14.2"
# ///
"""Writes the Workflows and agents lab's `runs.csv` from the runs `agents_runs.py` records, one
row a run: the variant, the task, its kind, the trial, the run's outcome, as `agents_runs.grade`
gives it, the seconds the run took, its requests to the chat model, and their tokens of prompt
and of reply, summed. The rows go by variant, as the lab builds them, then by task and trial.

    uv run tools/datasets/agents_data.py <runs.jsonl> <tasks.json> <runs.csv to write>
"""

import csv
import json
import sys
from pathlib import Path

VARIANTS = ["workflow", "agent", "router"]


def rows(runs: list[dict], tasks: list[dict]) -> list[list[object]]:
    kinds = {task["task"]: task["kind"] for task in tasks}
    order = {task["task"]: number for number, task in enumerate(tasks)}
    out = []
    for run in sorted(
        runs, key=lambda run: (VARIANTS.index(run["variant"]), order[run["task"]], run["trial"])
    ):
        requests = run["requests"]
        out.append(
            [
                run["variant"],
                run["task"],
                kinds[run["task"]],
                run["trial"],
                run["outcome"],
                f"{run['seconds']:.3f}",
                len(requests),
                sum(request.get("prompt_tokens", 0) for request in requests),
                sum(request.get("completion_tokens", 0) for request in requests),
            ]
        )
    return out


if __name__ == "__main__":
    runs_path, tasks_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    with open(runs_path, encoding="utf-8") as file:
        runs = [json.loads(line) for line in file if line.strip()]
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            [
                "variant",
                "task",
                "kind",
                "trial",
                "outcome",
                "seconds",
                "requests",
                "prompt_tokens",
                "completion_tokens",
            ]
        )
        writer.writerows(rows(runs, tasks))
