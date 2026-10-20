import csv
import json
from pathlib import Path

import numpy as np
import pytest

from hybrid import Hybrid

RECORDED = json.loads(Path("references/bm25.json").read_text(encoding="utf-8"))
# The vectors' numbers are stored times this.
SCALE = 32767
RRF = 60


def read(path):
    """A vector file's ids, and its whole numbers."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


@pytest.fixture(scope="module")
def desk():
    """The search of the help desk's passages, their vectors, and every tenth validation
    question with its vector."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = [row["text"] for row in csv.DictReader(file)]
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = [q for q in csv.DictReader(file) if q["set"] == "validation"]
    _, vectors = read("data/passage-vectors.csv")
    ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(ids, asked, strict=True))
    chosen = [(q["text"], vector_of[q["question"]]) for q in questions[::10]]
    return Hybrid(texts, vectors), vectors, chosen


@pytest.mark.id("tst_7b4g4w")
def test_question_words(desk):
    """Each question read into words as the passages are"""
    hybrid, _, asked = desk
    for question, _ in asked:
        assert np.array_equal(hybrid.bm25(question), hybrid.bm25(question.lower())), (
            question
        )


@pytest.mark.id("tst_0ls0lt")
def test_bm25(desk):
    """BM25's scores as bm25s gives them"""
    hybrid, _, _ = desk
    for case in RECORDED[::10]:
        found = hybrid.bm25(" ".join(case["words"]))
        if "scores" in case:
            assert found == pytest.approx(case["scores"], rel=1e-9, abs=1e-12)
        rows = [row for row, _ in case["top"]]
        assert found[rows] == pytest.approx(
            [score for _, score in case["top"]], rel=1e-9
        )


@pytest.mark.id("tst_tekzxd")
def test_similarity(desk):
    """Each passage's cosine, from the vectors' whole numbers"""
    hybrid, vectors, asked = desk
    for _, vector in asked:
        expected = (vectors @ vector) / SCALE**2
        np.testing.assert_allclose(
            hybrid.similarity(vector), expected, rtol=1e-12, atol=0
        )


@pytest.mark.id("tst_0jurhd")
def test_fused(desk):
    """The two rankings fused by their ranks"""
    hybrid, _, asked = desk
    for question, vector in asked:
        total = np.zeros(len(hybrid.counts))
        for scores in (hybrid.bm25(question), hybrid.similarity(vector)):
            ranking = np.argsort(-scores, kind="stable")
            total[ranking] += 1 / (RRF + np.arange(1, len(ranking) + 1))
        expected = np.argsort(-total, kind="stable")[:20].tolist()
        assert hybrid.search(question, vector, 20) == expected, question
