# /// script
# requires-python = "==3.14.2"
# dependencies = []
# ///
"""Builds the items `guardian.py` grades for Evals from the help desk's files: `passages.csv`,
`questions.csv`, `relevant.csv`, `runs.csv`, `replies.csv` and `human-replies.csv`.

Each reply of the current release's first sample is an item with the passages it was shown as
its context, in the form `multidoc2dial_replies.py` showed them. Each reply in
`human-replies.csv` is three: with its own passages, those of its question's page that hold its
answer; with the first passage of the `reranked` search that is on another page and holds none
of their texts; and with the own passages of another service's question: the question half the
file further on, going round from the end to the start, or the first after it from another
service. `to-grade.csv` holds each item, named by its question and then `current` and `1`, or
`human` and `own`, `other` or `swapped`, with its context and its reply.

    uv run tools/datasets/multidoc2dial_to_grade.py <folder of the help desk's files> \\
        <file to write>
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

from multidoc2dial_replies import RELEASES, ranked, read, shown_text


def build(folder: Path, out: Path) -> None:
    passages = {passage["passage"]: passage for passage in read(folder / "passages.csv")}
    questions = {question["question"]: question for question in read(folder / "questions.csv")}
    searches = ranked(folder)
    rows: list[list[object]] = []
    for reply in read(folder / "replies.csv"):
        if reply["release"] != "current" or reply["sample"] != "1":
            continue
        release = RELEASES[reply["release"]]
        shown = searches[release["search"], reply["question"]][: release["shown"]]
        item = f"{reply['question']}/{reply['release']}/{reply['sample']}"
        rows.append([item, shown_text([passages[p] for p in shown]), reply["reply"]])
    relevant: dict[str, list[str]] = defaultdict(list)
    for row in read(folder / "relevant.csv"):
        relevant[row["question"]].append(row["passage"])

    def own(question: dict[str, str]) -> list[dict[str, str]]:
        held = relevant[question["question"]]
        return [passages[p] for p in held if passages[p]["page"] == question["page"]]

    order = list(questions.values())
    for reply in read(folder / "human-replies.csv"):
        question = questions[reply["question"]]
        texts = {passages[p]["text"] for p in relevant[question["question"]]}
        other = next(
            passages[p]
            for p in searches["reranked", question["question"]]
            if passages[p]["page"] != question["page"] and passages[p]["text"] not in texts
        )
        start = (order.index(question) + len(order) // 2) % len(order)
        partner = next(
            q for q in order[start:] + order[:start] if q["domain"] != question["domain"]
        )
        contexts = (("own", own(question)), ("other", [other]), ("swapped", own(partner)))
        for name, context in contexts:
            item = f"{question['question']}/human/{name}"
            rows.append([item, shown_text(context), reply["reply"]])
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["item", "context", "reply"])
        writer.writerows(rows)


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
