import csv
import zlib
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pytest

from bm25 import BM25, words
from desk import Desk
from fuse import fused, nearest

MODEL = "Qwen3-Reranker-0.6B"
DEPTH = 20
K = 5
# The test questions' recall at K the search must reach.
FLOOR = 0.80


@dataclass
class Question:
    text: str
    vector: np.ndarray
    set: str
    relevant: set[int]


def read(path):
    """A vector file's ids, and its whole numbers."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


@pytest.fixture(scope="module")
def help_desk():
    """The help desk's passages, their vectors and index, its questions, and the score the
    reranker gave each question and passage it was asked about."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    texts = [passage["text"] for passage in passages]
    row_of = {passage["passage"]: row for row, passage in enumerate(passages)}
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for pair in csv.DictReader(file):
            relevant[pair["question"]].add(row_of[pair["passage"]])
    _, vectors = read("data/passage-vectors.csv")
    ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(ids, asked, strict=True))
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    text_of = {row["question"]: row["text"] for row in rows}
    questions = [
        Question(
            row["text"],
            vector_of[row["question"]],
            row["set"],
            relevant[row["question"]],
        )
        for row in rows
    ]
    scores = {}
    with open("data/rerank-scores.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            pair = (text_of[row["question"]], texts[row_of[row["passage"]]])
            scores[pair] = float(row["score"])
    index = BM25([words(text) for text in texts])
    return texts, vectors, index, questions, scores


def first_texts(texts, vectors, index, question):
    """The rows of the fused ranking's first DEPTH texts, each text's first row."""
    bm25 = np.argsort(-index.scores(words(question.text)), kind="stable")
    seen, rows = set(), []
    for row in fused([bm25, nearest(question.vector, vectors)]).tolist():
        if texts[row] not in seen:
            seen.add(texts[row])
            rows.append(row)
            if len(rows) == DEPTH:
                break
    return rows


@pytest.mark.id("tst_s19j01")
def test_recall(model, help_desk):
    """Recall at 5 of at least 0.80 on the test questions"""
    texts, vectors, _, questions, scores = help_desk
    model.ranks(scores)
    desk = Desk(model.client(), texts, vectors)
    tests = [question for question in questions if question.set == "test"]
    found = [
        not question.relevant.isdisjoint(desk.search(question.text, question.vector, K))
        for question in tests
    ]
    assert sum(found) / len(found) >= FLOOR


@pytest.mark.id("tst_5dar7f")
def test_request(model, help_desk):
    """One request a question, with the fused ranking's first 20 texts"""
    texts, vectors, index, questions, _ = help_desk
    model.ranks(lambda query, document: 0.5)
    desk = Desk(model.client(), texts, vectors)
    for question in questions[::50]:
        before = len(model.requests)
        desk.search(question.text, question.vector, K)
        assert len(model.requests) == before + 1, question.text
        request = model.requests[-1]
        assert request.path in ("/v1/rerank", "/v1/reranking")
        assert request.body["model"] == MODEL
        assert request.body["query"] == question.text
        rows = first_texts(texts, vectors, index, question)
        assert request.body["documents"] == [texts[row] for row in rows], question.text


@pytest.mark.id("tst_okpa2d")
def test_order(model, help_desk):
    """The highest scores first, a tie going to the passage ranked first"""
    texts, vectors, index, questions, _ = help_desk

    def score(query, document):
        return zlib.crc32(document.encode()) % 7 / 7

    model.ranks(score)
    desk = Desk(model.client(), texts, vectors)
    for question in questions[::50]:
        rows = first_texts(texts, vectors, index, question)
        order = sorted(
            range(len(rows)), key=lambda at: (-score("", texts[rows[at]]), at)
        )
        for k in (1, K, DEPTH):
            expected = [rows[at] for at in order[:k]]
            assert desk.search(question.text, question.vector, k) == expected, (
                question.text
            )


@pytest.mark.id("tst_54x2zy")
def test_fallback(model, help_desk):
    """The fused ranking when the reranker fails, drops the connection or doesn't answer"""
    texts, vectors, index, questions, _ = help_desk
    model.ranks(lambda query, document: 0.5)
    desk = Desk(model.client(), texts, vectors)
    question = questions[0]
    rows = first_texts(texts, vectors, index, question)
    for fail in (
        lambda: model.fails(503, "Loading model"),
        model.disconnects,
        model.hangs,
    ):
        fail()
        assert desk.search(question.text, question.vector, K) == rows[:K]
