# /// script
# requires-python = "==3.14.2"
# dependencies = []
# ///
"""Builds the data files of an Evals lab from the help desk's recorded files: `questions.csv`,
`relevant.csv` and `runs.csv`, as `multidoc2dial_evals.py`, `multidoc2dial_rerank.py` and
`multidoc2dial_runs.py` build them, and `replies.csv`, as `multidoc2dial_replies.py` records it.

For Test sets, `questions.csv` and `relevant.csv` as they are; `shown.csv`, the first 5
passages of the `reranked` search for each question, with their ranks from 1, as the current
release shows them; and `replies.csv`, the current release's first sample for each question,
with the reason the model stopped and the tokens it wrote.

    uv run tools/datasets/evals_data.py <folder of the recorded files> <lab> <folder to write in>
"""

import csv
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

SHOWN = 5


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def test_sets(recorded: Path, out: Path) -> None:
    for name in ("questions.csv", "relevant.csv"):
        shutil.copyfile(recorded / name, out / name)
    rows: list[list[object]] = [
        [row["question"], row["rank"], row["passage"]]
        for row in read(recorded / "runs.csv")
        if row["search"] == "reranked" and int(row["rank"]) <= SHOWN
    ]
    write(out / "shown.csv", ["question", "rank", "passage"], rows)
    rows = [
        [row["question"], row["reply"], row["finish"], row["tokens"]]
        for row in read(recorded / "replies.csv")
        if row["release"] == "current" and row["sample"] == "1"
    ]
    write(out / "replies.csv", ["question", "reply", "finish", "tokens"], rows)


LABS: dict[str, Callable[[Path, Path], None]] = {"test-sets": test_sets}

if __name__ == "__main__":
    recorded, lab, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    LABS[lab](recorded, out)
