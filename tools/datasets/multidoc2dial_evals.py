# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Builds the help desk files of Evals from MultiDoc2Dial's test dialogues, which the files of
Retrieval leave out, over the same pages and passages.

`passages.csv` holds the passages `multidoc2dial.py` builds, and `questions.csv` the opening
question of each test dialogue whose next turn is the agent's answer, given from parts of the
same page, chosen as `multidoc2dial.py` chooses Retrieval's questions: 340 of them, each with its
page and the page's domain. `relevant.csv` gives each question the passages that hold at least
half of a part of its answer, and every passage with the same text as one of them, and
`human-replies.csv` the reply the dataset's agent wrote from those parts.

nomic-embed-text-v1.5 at 8 bits, served by llama.cpp's llama-server b11734 as the labs serve it,
embeds each passage and each question as `multidoc2dial.py` embeds them, into
`passage-vectors.csv` and `question-vectors.csv`, so that `multidoc2dial_rerank.py` and
`multidoc2dial_runs.py` can search the passages for the questions as Retrieval's help desk does.

    uv run tools/datasets/multidoc2dial_evals.py <folder to write in> <llama-server> [<downloads>]

<llama-server> is llama.cpp's server, release b11734, such as the one `uv run sulba.py model`
fetches into `sulba` in the cache folder. The dataset's zip comes to 6.9 MB and the model to
146 MB. Given a folder of downloads, the script keeps them there for the next run; without one,
it downloads them to a temporary folder.
"""

import sys
import tempfile
from pathlib import Path

import multidoc2dial as dataset
import numpy as np


def build(out: Path, server: Path, downloads: Path) -> None:
    archive = dataset.download(
        dataset.DATASET, dataset.DATASET_SHA256, downloads / "multidoc2dial.zip"
    )
    model = dataset.download(
        dataset.MODEL, dataset.MODEL_SHA256, downloads / "nomic-embed-text-v1.5.Q8_0.gguf"
    )
    docs, dialogues = dataset.contents(archive, ("test",))
    pages = dataset.pages_of(docs)
    passages = dataset.passages_of(pages)
    questions = dataset.opening_questions(dialogues["test"], pages)
    relevant: list[list[object]] = []
    for number, question in enumerate(questions, start=1):
        question["question"] = f"q{number}"
        held = dataset.holding(question, passages)
        relevant += [[question["question"], passage] for passage in held]
    dataset.write_passages(out / "passages.csv", passages, pages)
    rows: list[list[object]] = []
    for question in questions:
        page = pages[question["doc"]]
        rows.append([question["question"], page["page"], page["domain"], question["text"]])
    dataset.write(out / "questions.csv", ["question", "page", "domain", "text"], rows)
    dataset.write(out / "relevant.csv", ["question", "passage"], relevant)
    rows = [[question["question"], question["reply"]] for question in questions]
    dataset.write(out / "human-replies.csv", ["question", "reply"], rows)
    with dataset.served(server, model, downloads / "llama-server.log") as embed:
        texts = [dataset.DOCUMENT + passage["text"] for passage in passages]
        passage_vectors = np.array([embed(text) for text in texts])
        texts = [dataset.QUERY + question["text"] for question in questions]
        question_vectors = np.array([embed(text) for text in texts])
    ids = [passage["passage"] for passage in passages]
    dataset.write_vectors(out / "passage-vectors.csv", "passage", ids, passage_vectors)
    ids = [question["question"] for question in questions]
    dataset.write_vectors(out / "question-vectors.csv", "question", ids, question_vectors)


if __name__ == "__main__":
    out, server = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 3:
        build(out, server, Path(sys.argv[3]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            build(out, server, Path(downloads))
