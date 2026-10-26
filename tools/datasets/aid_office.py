# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Builds the aid office's files for the Intermediate capstone from MultiDoc2Dial: the federal
student aid pages the office answers from, and the questions people opened their dialogues about
them with, chosen as `multidoc2dial.py` chooses Retrieval's.

`pages.csv` holds each student aid page with its title and text, as `multidoc2dial.py` writes
them. `questions.csv` holds those of Retrieval's questions whose page is one of them, numbered
again in the same order, each with its set and its page, and `answers.csv` each part of each
question's answer, as its first character and the one after its last on its page's text.

    uv run tools/datasets/aid_office.py <folder to write in> [<downloads>]

Given a folder of downloads, the script keeps the dataset's zip there for the next run; without
one, it downloads it to a temporary folder.
"""

import sys
import tempfile
from pathlib import Path

import multidoc2dial as dataset

DOMAIN = "studentaid"


def build(out: Path, downloads: Path) -> None:
    archive = dataset.download(
        dataset.DATASET, dataset.DATASET_SHA256, downloads / "multidoc2dial.zip"
    )
    docs, dialogues = dataset.contents(archive, ("train", "validation"))
    pages = dataset.pages_of(docs)
    found = {
        split: dataset.opening_questions(by_domain, pages) for split, by_domain in dialogues.items()
    }
    questions = [
        {**found["train"][i], "set": "validation"} for i in dataset.drawn_for_validation(found)
    ]
    questions += [{**question, "set": "test"} for question in found["validation"]]
    questions = [question for question in questions if pages[question["doc"]]["domain"] == DOMAIN]
    for number, question in enumerate(questions, start=1):
        question["question"] = f"q{number}"
    rows = [
        [page["page"], page["title"], page["text"]]
        for page in pages.values()
        if page["domain"] == DOMAIN
    ]
    dataset.write(out / "pages.csv", ["page", "title", "text"], rows)
    rows = [
        [question["question"], question["set"], pages[question["doc"]]["page"], question["text"]]
        for question in questions
    ]
    dataset.write(out / "questions.csv", ["question", "set", "page", "text"], rows)
    rows = [
        [question["question"], start, end]
        for question in questions
        for start, end in sorted(question["parts"])
    ]
    dataset.write(out / "answers.csv", ["question", "start", "end"], rows)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 2:
        build(out, Path(sys.argv[2]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            build(out, Path(downloads))
