# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Records each of the help desk's searches as a run: its first 20 passages for each question,
from the files `multidoc2dial.py` and `multidoc2dial_rerank.py` build: `passages.csv`,
`questions.csv`, `passage-vectors.csv`, `question-vectors.csv` and `rerank-scores.csv`.

The searches, each a ranking of the passages for a question, a tie going to the passage that
comes first in `passages.csv`:

- `bm25`: BM25 over their words, Lucene's, as bm25s gives it by default, with k1 = 1.5 and
  b = 0.75, worked out in float64. A word is a run of letters, digits and underscores,
  lowercased.
- `vectors`: the dot product of their vectors with the question's, in whole numbers.
- `fused`: reciprocal rank fusion of the two, with k = 60, summed in fractions.
- `fused-once`: the fused ranking with each text once, as the first passage that holds it.
- `reranked`: the fused ranking's first 20 texts, each as the first passage that holds it, in
  the order of the scores Qwen3-Reranker-0.6B gave them in `rerank-scores.csv`, highest first, a
  tie going to the one ranked first.
- `reranked-bm25` and `reranked-vectors`: the same, from the first 20 texts of BM25's ranking
  and of the vectors'.
- `reranked-copies`: the fused ranking's first 20 passages, two with the same text included,
  in the order of their scores.
- `confident`: the passages of `reranked` the reranker scores at 0.5 or more, so that a question
  can have none.

`runs.csv` holds, for each search and each question, its first 20 passages, each with its rank
from 1, and no row for a question a search gives no passage.

    uv run tools/datasets/multidoc2dial_runs.py <folder of the help desk's files> <file to write>
"""

import csv
import math
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import numpy as np

WORD = re.compile(r"\w+")
K1, B = 1.5, 0.75
# Reciprocal rank fusion's constant, the texts each reranked search sends the reranker, the
# passages each search shows, and the score a passage of `confident` reaches.
K = 60
TEXTS = 20
SHOWN = 20
CONFIDENT = 0.5
# How many of the fused ranking's first rows are put in order in fractions, and how close two
# BM25 scores may be before a system's logarithm could put them the other way.
EXACT = 80
CLEAR = 1e-9
SEARCHES = [
    "bm25",
    "vectors",
    "fused",
    "fused-once",
    "reranked",
    "reranked-bm25",
    "reranked-vectors",
    "reranked-copies",
    "confident",
]


def read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_vectors(path: Path) -> tuple[list[str], np.ndarray]:
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


class BM25:
    """Lucene's BM25 over the passages' words, in float64."""

    def __init__(self, texts: list[str]) -> None:
        passages = [words(text) for text in texts]
        lengths = np.array([len(passage) for passage in passages], dtype=np.float64)
        self.norm = K1 * (1 - B + B * lengths / lengths.mean())
        self.counts = [Counter(passage) for passage in passages]
        held = Counter(word for passage in passages for word in set(passage))
        count = len(passages)
        self.idf = {word: math.log(1 + (count - n + 0.5) / (n + 0.5)) for word, n in held.items()}

    def ranking(self, question: str) -> list[int]:
        scores = np.zeros(len(self.counts))
        for word in words(question):
            if word in self.idf:
                tf = np.array([count[word] for count in self.counts], dtype=np.float64)
                scores += self.idf[word] * tf / (tf + self.norm)
        order = np.argsort(-scores, kind="stable").tolist()
        for first, second in pairwise(order[: EXACT + 1]):
            higher, lower = scores[first], scores[second]
            if higher != lower and higher - lower <= CLEAR * higher:
                sys.exit(f"{question!r}: two BM25 scores too close to put in order")
        return order


def fused(rankings: list[list[int]]) -> list[int]:
    """The first EXACT rows of reciprocal rank fusion, in fractions. Sums in floats find the
    candidates, which differ from the fractions' by far less than any two ranks' shares."""
    total = np.zeros(len(rankings[0]))
    for ranking in rankings:
        total[ranking] += 1 / (K + np.arange(1, len(ranking) + 1))
    candidates = np.argsort(-total, kind="stable")[: 2 * EXACT].tolist()
    places = [dict(zip(ranking, range(1, len(ranking) + 1), strict=True)) for ranking in rankings]
    exact = {row: sum(Fraction(1, K + place[row]) for place in places) for row in candidates}
    return sorted(candidates, key=lambda row: (-exact[row], row))[:EXACT]


def once(ranking: list[int], texts: list[str]) -> list[int]:
    """The first row of each text, in the ranking's order."""
    seen: set[str] = set()
    rows = []
    for row in ranking:
        if texts[row] not in seen:
            seen.add(texts[row])
            rows.append(row)
    return rows


def reranked(rows: list[int], scores: dict[int, float]) -> list[int]:
    """The rows by the reranker's scores, highest first, a tie going to the one ranked first."""
    places = sorted(range(len(rows)), key=lambda at: (-scores[rows[at]], at))
    return [rows[at] for at in places]


def main(folder: Path, out: Path) -> None:
    passages = read(folder / "passages.csv")
    ids = [passage["passage"] for passage in passages]
    row_of = {passage: row for row, passage in enumerate(ids)}
    texts = [passage["text"] for passage in passages]
    scores: dict[str, dict[int, float]] = defaultdict(dict)
    for score in read(folder / "rerank-scores.csv"):
        scores[score["question"]][row_of[score["passage"]]] = float(score["score"])
    bm25 = BM25(texts)
    passage_ids, vectors = read_vectors(folder / "passage-vectors.csv")
    assert passage_ids == ids
    question_ids, asked = read_vectors(folder / "question-vectors.csv")
    vector_of = dict(zip(question_ids, asked, strict=True))
    runs: dict[str, dict[str, list[int]]] = {search: {} for search in SEARCHES}
    for question in read(folder / "questions.csv"):
        name = question["question"]
        scored = scores[name]
        by_words = bm25.ranking(question["text"])
        nearest = np.argsort(-(vectors @ vector_of[name]), kind="stable").tolist()
        both = fused([by_words, nearest])
        first = reranked(once(both, texts)[:TEXTS], scored)
        runs["bm25"][name] = by_words
        runs["vectors"][name] = nearest
        runs["fused"][name] = both
        runs["fused-once"][name] = once(both, texts)
        runs["reranked"][name] = first
        runs["reranked-bm25"][name] = reranked(once(by_words, texts)[:TEXTS], scored)
        runs["reranked-vectors"][name] = reranked(once(nearest, texts)[:TEXTS], scored)
        runs["reranked-copies"][name] = reranked(both[:TEXTS], scored)
        runs["confident"][name] = [row for row in first if scored[row] >= CONFIDENT]
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["search", "question", "rank", "passage"])
        for search, run in runs.items():
            for name, rows in run.items():
                for rank, row in enumerate(rows[:SHOWN], start=1):
                    writer.writerow([search, name, rank, ids[row]])


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
