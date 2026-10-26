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
`other-questions.csv` holds the rest of Retrieval's questions, about the other three services'
pages, numbered again in the same order, each with its set.

`passages.csv` holds the student aid pages' passages, as `multidoc2dial.py` cuts them, numbered
again in the same order, each with its page and the page's title. nomic-embed-text-v1.5 at 8
bits, served by llama.cpp's llama-server b11734 as the labs serve it, embeds each passage after
`search_document: ` and each question, the office's and the others, after `search_query: `, one
text a request, into `passage-vectors.csv` and `question-vectors.csv`, each number times 32,767,
rounded to a whole number.

    uv run tools/datasets/aid_office.py <folder to write in> <llama-server> [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. Given a folder of downloads, the script keeps the
dataset's zip and the model there for the next run; without one, it downloads them to a
temporary folder.
"""

import sys
import tempfile
from pathlib import Path

import multidoc2dial as dataset
import numpy as np

DOMAIN = "studentaid"


def build(out: Path, server: Path, downloads: Path) -> None:
    archive = dataset.download(
        dataset.DATASET, dataset.DATASET_SHA256, downloads / "multidoc2dial.zip"
    )
    model = dataset.download(
        dataset.MODEL,
        dataset.MODEL_SHA256,
        downloads / "nomic-embed-text-v1.5.Q8_0.gguf",
    )
    docs, dialogues = dataset.contents(archive, ("train", "validation"))
    pages = dataset.pages_of(docs)
    found = {
        split: dataset.opening_questions(by_domain, pages) for split, by_domain in dialogues.items()
    }
    every = [
        {**found["train"][i], "set": "validation"} for i in dataset.drawn_for_validation(found)
    ]
    every += [{**question, "set": "test"} for question in found["validation"]]
    questions = [question for question in every if pages[question["doc"]]["domain"] == DOMAIN]
    others = [question for question in every if pages[question["doc"]]["domain"] != DOMAIN]
    for number, question in enumerate(questions, start=1):
        question["question"] = f"q{number}"
    for number, question in enumerate(others, start=1):
        question["question"] = f"o{number}"
    passages = [
        passage
        for passage in dataset.passages_of(pages)
        if pages[passage["doc"]]["domain"] == DOMAIN
    ]
    for number, passage in enumerate(passages, start=1):
        passage["passage"] = f"p{number}"
    rows = [
        [page["page"], page["title"], page["text"]]
        for page in pages.values()
        if page["domain"] == DOMAIN
    ]
    dataset.write(out / "pages.csv", ["page", "title", "text"], rows)
    rows = [
        [
            question["question"],
            question["set"],
            pages[question["doc"]]["page"],
            question["text"],
        ]
        for question in questions
    ]
    dataset.write(out / "questions.csv", ["question", "set", "page", "text"], rows)
    rows = [
        [question["question"], start, end]
        for question in questions
        for start, end in sorted(question["parts"])
    ]
    dataset.write(out / "answers.csv", ["question", "start", "end"], rows)
    rows = [[question["question"], question["set"], question["text"]] for question in others]
    dataset.write(out / "other-questions.csv", ["question", "set", "text"], rows)
    rows = [
        [
            passage["passage"],
            pages[passage["doc"]]["page"],
            pages[passage["doc"]]["title"],
            passage["text"],
        ]
        for passage in passages
    ]
    dataset.write(out / "passages.csv", ["passage", "page", "title", "text"], rows)
    asked = questions + others
    with dataset.served(server, model, downloads / "llama-server.log") as embed:
        passage_vectors = np.array(
            [embed(dataset.DOCUMENT + passage["text"]) for passage in passages]
        )
        question_vectors = np.array([embed(dataset.QUERY + question["text"]) for question in asked])
    ids = [passage["passage"] for passage in passages]
    dataset.write_vectors(out / "passage-vectors.csv", "passage", ids, passage_vectors)
    ids = [question["question"] for question in asked]
    dataset.write_vectors(out / "question-vectors.csv", "question", ids, question_vectors)


if __name__ == "__main__":
    out, server = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 3:
        build(out, server, Path(sys.argv[3]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            build(out, server, Path(downloads))
