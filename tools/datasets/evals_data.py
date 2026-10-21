# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
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

For Regression gates, `questions.csv`, the questions of Test sets' test set, as its first stage
splits them; `relevant.csv`, their passages that hold the answer; and `replies.csv`, every
release's replies to them, by release and sample, with the reason the model stopped, the
current release's samples after the fifth as the release `rerun`, numbered from 1.

    uv run tools/datasets/evals_data.py <folder of the recorded files> <lab> <folder to write in>
"""

import csv
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np

SHOWN = 5
RANKED = 10
SERVICES = ["dmv", "ssa", "studentaid", "va"]
SHARE = 0.5
RERUN = 5


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


def test_set(questions: list[dict[str, str]]) -> list[dict[str, str]]:
    """The test set of Test sets, in the file's order: each question once, by its words, and
    each service's pages drawn whole in the order `numpy.random.default_rng(0)` permutes
    them until they hold half its questions."""
    seen: set[tuple[str, ...]] = set()
    kept: list[dict[str, str]] = []
    for question in questions:
        key = tuple(re.findall(r"\w+", question["text"].lower()))
        if key not in seen:
            seen.add(key)
            kept.append(question)
    rng = np.random.default_rng(0)
    test: set[str] = set()
    for service in SERVICES:
        theirs = [question for question in kept if question["domain"] == service]
        pages = list(dict.fromkeys(question["page"] for question in theirs))
        held = 0
        for index in rng.permutation(len(pages)):
            if held >= SHARE * len(theirs):
                break
            on_page = [q["question"] for q in theirs if q["page"] == pages[index]]
            test.update(on_page)
            held += len(on_page)
    return [question for question in kept if question["question"] in test]


def regression_gates(recorded: Path, out: Path) -> None:
    questions = test_set(read(recorded / "questions.csv"))
    names = {question["question"] for question in questions}
    write(
        out / "questions.csv",
        ["question", "page", "domain", "text"],
        [[q["question"], q["page"], q["domain"], q["text"]] for q in questions],
    )
    rows: list[list[object]] = [
        [row["question"], row["passage"]]
        for row in read(recorded / "relevant.csv")
        if row["question"] in names
    ]
    write(out / "relevant.csv", ["question", "passage"], rows)
    rows = []
    for row in read(recorded / "replies.csv"):
        if row["question"] in names:
            release, sample = row["release"], int(row["sample"])
            if release == "current" and sample > RERUN:
                release, sample = "rerun", sample - RERUN
            rows.append([row["question"], release, sample, row["reply"], row["finish"]])
    write(out / "replies.csv", ["question", "release", "sample", "reply", "finish"], rows)


LABS: dict[str, Callable[[Path, Path], None]] = {
    "test-sets": test_sets,
    "grading-with-a-model": grading_with_a_model,
    "regression-gates": regression_gates,
}

if __name__ == "__main__":
    recorded, lab, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    LABS[lab](recorded, out)
