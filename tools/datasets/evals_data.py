# /// script
# requires-python = "==3.14.2"
# dependencies = []
# ///
"""Builds the data files of an Evals lab from the help desk's recorded files: `passages.csv`,
`questions.csv`, `relevant.csv`, `human-replies.csv` and `runs.csv`, as
`multidoc2dial_evals.py`, `multidoc2dial_rerank.py` and `multidoc2dial_runs.py` build them;
`replies.csv`, as `multidoc2dial_replies.py` records it; `grades.csv`, the grades `guardian.py`
records for the items `multidoc2dial_to_grade.py` builds; and `begin.csv` and
`begin-grades.csv`, as `begin.py` and `guardian.py` build them.

For Test sets, `questions.csv` and `relevant.csv` as they are; `shown.csv`, the first 5
passages of the `reranked` search for each question, with their ranks from 1, as the current
release shows them; and `replies.csv`, the current release's first sample for each question,
with the reason the model stopped and the tokens it wrote.

For Grading with a model, `begin.csv`, `begin-grades.csv`, `passages.csv`, `questions.csv`,
`relevant.csv` and `human-replies.csv` as they are; `ranked.csv`, the first 10 passages of the
`reranked` search for each question; `human-grades.csv`, the grades of each reply in
`human-replies.csv` with its own passages, with another page's and with another service's; and
`replies.csv` and `grades.csv`, the current release's first sample for each question and its
grades.

    uv run tools/datasets/evals_data.py <folder of the recorded files> <lab> <folder to write in>
"""

import csv
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

SHOWN = 5
RANKED = 10


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def reranked(recorded: Path, out: Path, depth: int) -> None:
    """Writes the first passages of the `reranked` search for each question, with their ranks
    from 1."""
    rows: list[list[object]] = [
        [row["question"], row["rank"], row["passage"]]
        for row in read(recorded / "runs.csv")
        if row["search"] == "reranked" and int(row["rank"]) <= depth
    ]
    write(out, ["question", "rank", "passage"], rows)


def test_sets(recorded: Path, out: Path) -> None:
    for name in ("questions.csv", "relevant.csv"):
        shutil.copyfile(recorded / name, out / name)
    reranked(recorded, out / "shown.csv", SHOWN)
    rows = [
        [row["question"], row["reply"], row["finish"], row["tokens"]]
        for row in read(recorded / "replies.csv")
        if row["release"] == "current" and row["sample"] == "1"
    ]
    write(out / "replies.csv", ["question", "reply", "finish", "tokens"], rows)


def grading_with_a_model(recorded: Path, out: Path) -> None:
    for name in (
        "begin.csv",
        "begin-grades.csv",
        "passages.csv",
        "questions.csv",
        "relevant.csv",
        "human-replies.csv",
    ):
        shutil.copyfile(recorded / name, out / name)
    reranked(recorded, out / "ranked.csv", RANKED)
    grades = {row["item"]: row for row in read(recorded / "grades.csv")}
    rows: list[list[object]] = []
    for question in read(recorded / "questions.csv"):
        for context in ("own", "other", "swapped"):
            grade = grades[f"{question['question']}/human/{context}"]
            rows.append([question["question"], context, grade["yes"], grade["no"]])
    write(out / "human-grades.csv", ["question", "context", "yes", "no"], rows)
    replies = [
        row
        for row in read(recorded / "replies.csv")
        if row["release"] == "current" and row["sample"] == "1"
    ]
    rows = [[row["question"], row["reply"]] for row in replies]
    write(out / "replies.csv", ["question", "reply"], rows)
    rows = []
    for row in replies:
        grade = grades[f"{row['question']}/current/1"]
        rows.append([row["question"], grade["yes"], grade["no"]])
    write(out / "grades.csv", ["question", "yes", "no"], rows)


LABS: dict[str, Callable[[Path, Path], None]] = {
    "test-sets": test_sets,
    "grading-with-a-model": grading_with_a_model,
}

if __name__ == "__main__":
    recorded, lab, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    LABS[lab](recorded, out)
