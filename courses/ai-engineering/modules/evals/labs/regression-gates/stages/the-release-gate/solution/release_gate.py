"""The help desk's release gate, as CI runs it on every release before it ships."""

import csv
import sys
from collections import defaultdict

import numpy as np

from gate import Verdict, gate
from samples import cites_answer

MOST = 100
SAMPLES = [1, 2, 3, 4, 5]


def scored(
    replies: list[dict[str, str]],
    relevant: dict[str, set[str]],
    questions: list[str],
    release: str,
    samples: list[int],
) -> dict[str, np.ndarray]:
    """Each of the release's scores, a row for each question and a column for each
    sample."""
    found = {
        (row["question"], int(row["sample"])): row
        for row in replies
        if row["release"] == release
    }
    rows = [[found[question, sample] for sample in samples] for question in questions]
    return {
        "cites_answer": np.array(
            [
                [cites_answer(row["reply"], relevant[question]) for row in theirs]
                for question, theirs in zip(questions, rows, strict=True)
            ]
        ),
        "finished": np.array(
            [[float(row["finish"] == "stop") for row in theirs] for theirs in rows]
        ),
        "brief": np.array(
            [
                [float(len(row["reply"].split()) <= MOST) for row in theirs]
                for theirs in rows
            ]
        ),
    }


def check(
    baseline: dict[str, np.ndarray],
    candidate: dict[str, np.ndarray],
    pages: list[str],
    alpha: float,
) -> dict[str, Verdict]:
    """A verdict on each score, each at alpha over the number of scores."""
    level = alpha / len(baseline)
    return {
        name: gate(baseline[name], candidate[name], pages, level) for name in baseline
    }


def report(verdicts: dict[str, Verdict]) -> list[str]:
    """A line for each score, then the gate's decision."""
    lines = [
        f"{name}: {verdict.change:+.3f} ({verdict.low:+.3f} to {verdict.high:+.3f}), "
        + ("ships" if verdict.ships else "stopped")
        for name, verdict in verdicts.items()
    ]
    ships = all(verdict.ships for verdict in verdicts.values())
    return [*lines, "ships" if ships else "stopped"]


def read(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def main(arguments: list[str]) -> int:
    """The gate on the candidate against the baseline, from a file of replies: prints the
    report and returns 1 when it stops the candidate and 0 when it ships."""
    path, baseline, candidate = arguments
    questions = read("data/questions.csv")
    names = [question["question"] for question in questions]
    pages = [question["page"] for question in questions]
    relevant: dict[str, set[str]] = defaultdict(set)
    for row in read("data/relevant.csv"):
        relevant[row["question"]].add(row["passage"])
    replies = read(path)
    verdicts = check(
        scored(replies, relevant, names, baseline, SAMPLES),
        scored(replies, relevant, names, candidate, SAMPLES),
        pages,
        0.05,
    )
    lines = report(verdicts)
    print("\n".join(lines))
    return 0 if lines[-1] == "ships" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
