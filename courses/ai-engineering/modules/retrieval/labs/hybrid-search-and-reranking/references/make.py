# /// script
# requires-python = "==3.14.2"
# dependencies = ["bm25s==0.3.14", "numpy==2.4.6"]
# ///
"""Records how bm25s scores the help desk's passages for its validation questions, for the
lab's tests.

bm25s's default BM25, Lucene's, with k1 = 1.5 and b = 0.75, is worked out in float64 on the
passages' words and each question's: runs of letters, digits and underscores, lowercased.

bm25.json holds, for each validation question, its words and its 20 passages with the highest
scores, each as its row in passages.csv beside its score, a tie going to the earlier row, and
for the first three, every passage's score.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import csv
import json
import re
import sys
from pathlib import Path

import bm25s
import numpy as np

WORD = re.compile(r"\w+")
TOP = 20
EVERY = 3


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def main(out: Path, data: Path) -> None:
    with open(data / "passages.csv", encoding="utf-8", newline="") as file:
        passages = [words(row["text"]) for row in csv.DictReader(file)]
    with open(data / "questions.csv", encoding="utf-8", newline="") as file:
        questions = [row for row in csv.DictReader(file) if row["set"] == "validation"]
    retriever = bm25s.BM25(k1=1.5, b=0.75, method="lucene", dtype="float64")
    retriever.index(passages, show_progress=False)
    recorded = []
    for number, question in enumerate(questions):
        asked = words(question["text"])
        scores = retriever.get_scores(asked)
        top = np.argsort(-scores, kind="stable")[:TOP].tolist()
        case = {
            "question": question["question"],
            "words": asked,
            "top": [[row, float(scores[row])] for row in top],
        }
        if number < EVERY:
            case["scores"] = scores.tolist()
        recorded.append(case)
    with open(out / "bm25.json", "w", encoding="utf-8", newline="\n") as file:
        json.dump(recorded, file)
        file.write("\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
