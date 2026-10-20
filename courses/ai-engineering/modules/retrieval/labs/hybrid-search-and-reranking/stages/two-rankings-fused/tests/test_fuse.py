import csv
from collections import defaultdict
from fractions import Fraction

import numpy as np
import pytest

from bm25 import BM25, words
from fuse import fused, nearest, recall


def read(path):
    """A vector file's ids, and its whole numbers."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


@pytest.fixture(scope="module")
def validation():
    """Each validation question's BM25 ranking, its vectors' ranking, and its relevant
    passages, as rows of passages.csv."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    row_of = {passage["passage"]: row for row, passage in enumerate(passages)}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = [q for q in csv.DictReader(file) if q["set"] == "validation"]
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for pair in csv.DictReader(file):
            relevant[pair["question"]].add(row_of[pair["passage"]])
    _, vectors = read("data/passage-vectors.csv")
    ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(ids, asked, strict=True))
    index = BM25([words(passage["text"]) for passage in passages])
    return [
        (
            np.argsort(-index.scores(words(q["text"])), kind="stable"),
            np.argsort(-(vectors @ vector_of[q["question"]]), kind="stable"),
            relevant[q["question"]],
        )
        for q in questions
    ]


def exact(rankings, k=60):
    """Reciprocal rank fusion in fractions, a tie going to the earlier row."""
    total = defaultdict(Fraction)
    for ranking in rankings:
        for rank, row in enumerate(ranking.tolist(), start=1):
            total[row] += Fraction(1, k + rank)
    return sorted(total, key=lambda row: (-total[row], row))


@pytest.mark.id("tst_u81h9l")
def test_nearest():
    """The most similar first, a tie going to the earlier row"""
    vectors = np.array([[1, 0], [3, 4], [0, 5], [3, 4]], dtype=np.int64)
    assert nearest(np.array([0, 1]), vectors).tolist() == [2, 1, 3, 0]


@pytest.mark.id("tst_zznu73")
def test_fused():
    """Each row by its reciprocal ranks, summed"""
    first = np.array([2, 0, 1, 3])
    second = np.array([0, 3, 2, 1])
    assert fused([first, second]).tolist() == [0, 2, 3, 1]
    assert fused([first, second], k=0).tolist() == [0, 2, 3, 1]
    assert fused([first, first[::-1]], k=1).tolist() == [2, 3, 0, 1]
    assert fused([first]).tolist() == first.tolist()


@pytest.mark.id("tst_9s0s7z")
def test_ties():
    """A tie going to the earlier row"""
    assert fused([np.array([1, 0]), np.array([0, 1])]).tolist() == [0, 1]
    assert fused([np.array([3, 2, 1, 0]), np.array([0, 1, 2, 3])]).tolist() == [
        0,
        3,
        1,
        2,
    ]


@pytest.mark.id("tst_drkp5v")
def test_recall():
    """The share of questions with a relevant row among the first k"""
    rankings = [np.array([3, 1, 2, 0]), np.array([0, 1, 2, 3]), np.array([2, 0, 1, 3])]
    relevant = [{1}, {3}, {0, 2}]
    assert recall(rankings, relevant, 1) == pytest.approx(1 / 3)
    assert recall(rankings, relevant, 2) == pytest.approx(2 / 3)
    assert recall(rankings, relevant, 4) == 1


@pytest.mark.id("tst_5iclr4")
def test_validation(validation):
    """Every tenth validation question's two rankings fused, and their recall"""
    asked = validation[::10]
    for bm25, vectors, _ in asked:
        assert fused([bm25, vectors])[:20].tolist() == exact([bm25, vectors])[:20]
    rankings = [fused([bm25, vectors]) for bm25, vectors, _ in asked]
    relevant = [rows for *_, rows in asked]
    hits = [not rows.isdisjoint(exact([b, v])[:5]) for b, v, rows in asked]
    assert recall(rankings, relevant, 5) == pytest.approx(sum(hits) / len(hits))
