# /// script
# requires-python = "==3.14.2"
# ///
"""Writes the Memory and sub-agents lab's `runs.csv` from the runs `agents_long_runs.py` records,
in one file or more: a row for each part of each run, with the variant, the conversation, the
trial, the part, from 1, its kind and its outcome, as `agents_long_runs.grade` gives it, and of
the chat requests sent while it lasted: the seconds they took; the agent's requests, their
tokens of prompt, the prompt's tokens the server had cached, the largest prompt, and the tools
the model called in each request, a request's tools separated by spaces and the requests by |;
the agent's requests the memory cleared tool results before, and its summaries; the
researchers' requests and their tokens of prompt; and refused, "context" when the server
refused a request for its size, "other" for any other error that ended the run there, or empty.
The rows go by variant, as the lab builds them, then by conversation, trial and part.

    uv run tools/datasets/agents_long_data.py <conversations.json> <runs.csv to write> \\
        <runs.jsonl>...
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any

VARIANTS = ["whole", "memory", "researchers"]
COLUMNS = [
    "variant",
    "conversation",
    "trial",
    "part",
    "kind",
    "outcome",
    "seconds",
    "requests",
    "prompt_tokens",
    "cached_tokens",
    "largest_prompt",
    "calls",
    "cleared",
    "summaries",
    "researcher_requests",
    "researcher_prompt_tokens",
    "refused",
]


def rows(runs: list[dict[str, Any]], conversations: list[dict[str, Any]]) -> list[list[object]]:
    held = {each["conversation"]: each for each in conversations}
    order = {each["conversation"]: n for n, each in enumerate(conversations)}
    out = []
    for run in sorted(
        runs,
        key=lambda run: (VARIANTS.index(run["variant"]), order[run["conversation"]], run["trial"]),
    ):
        parts = held[run["conversation"]]["parts"]
        agent = [request for request in run["requests"] if request.get("role") == "agent"]
        # What the memory did before each of the agent's requests it got a reply to: a request
        # the server refused, which ends the run, has none.
        fitted = dict(zip((id(request) for request in agent), run.get("fitted", []), strict=False))
        ended = next((n for n, part in enumerate(run["parts"]) if part["outcome"] == "error"), None)
        turn = 0
        for n, (part, graded) in enumerate(zip(parts, run["parts"], strict=True)):
            turns = range(turn, turn + len(part["messages"]))
            turn += len(part["messages"])
            sent = [request for request in run["requests"] if request.get("turn") in turns]
            mine = [request for request in sent if request.get("role") == "agent"]
            asked = [request for request in sent if request.get("role") == "researcher"]
            refused = ""
            if n == ended:
                sized = any("context" in request.get("refused", "") for request in sent)
                refused = "context" if sized else "other"
            out.append(
                [
                    run["variant"],
                    run["conversation"],
                    run["trial"],
                    n + 1,
                    graded["kind"],
                    graded["outcome"],
                    f"{sum(request['seconds'] for request in sent):.3f}",
                    len(mine),
                    sum(request.get("prompt_tokens", 0) for request in mine),
                    sum(request.get("cached_tokens", 0) for request in mine),
                    max((request.get("prompt_tokens", 0) for request in mine), default=0),
                    "|".join(" ".join(request.get("calls", [])) for request in mine),
                    sum(fitted.get(id(request)) == "cleared" for request in mine),
                    sum(request.get("role") == "summary" for request in sent),
                    len(asked),
                    sum(request.get("prompt_tokens", 0) for request in asked),
                    refused,
                ]
            )
    return out


if __name__ == "__main__":
    conversations_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    runs = []
    for runs_path in sys.argv[3:]:
        with open(runs_path, encoding="utf-8") as file:
            runs += [json.loads(line) for line in file if line.strip()]
    conversations = json.loads(conversations_path.read_text(encoding="utf-8"))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows(runs, conversations))
